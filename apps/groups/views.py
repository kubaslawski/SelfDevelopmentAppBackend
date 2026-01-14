"""
Views for Groups app.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Group, GroupInvitation, GroupMembership
from .permissions import (
    CanInviteToGroup,
    IsGroupAdmin,
    IsGroupMember,
    IsGroupOwner,
    IsInvitationRecipient,
)
from .serializers import (
    AcceptInvitationSerializer,
    CreateInvitationSerializer,
    GroupCreateSerializer,
    GroupDetailSerializer,
    GroupInvitationSerializer,
    GroupListSerializer,
    GroupMembershipSerializer,
    UpdateMembershipRoleSerializer,
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(tags=["Groups"]),
    retrieve=extend_schema(tags=["Groups"]),
    create=extend_schema(tags=["Groups"]),
    update=extend_schema(tags=["Groups"]),
    partial_update=extend_schema(tags=["Groups"]),
    destroy=extend_schema(tags=["Groups"]),
)
class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing groups.
    
    List: Shows groups user is member of + public groups
    Create: Create a new group (user becomes owner)
    Update: Edit group (admin only)
    Delete: Delete group (owner only)
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Group.objects.filter(
            Q(owner=user) |
            Q(memberships__user=user, memberships__is_active=True) |
            Q(is_public=True)
        ).annotate(
            member_count=Count(
                "memberships",
                filter=Q(memberships__is_active=True),
            )
        ).distinct().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return GroupListSerializer
        if self.action == "create":
            return GroupCreateSerializer
        return GroupDetailSerializer

    def get_permissions(self):
        if self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), IsGroupAdmin()]
        if self.action == "destroy":
            return [IsAuthenticated(), IsGroupOwner()]
        return [IsAuthenticated()]

    @extend_schema(tags=["Groups"])
    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """List all members of a group."""
        group = self.get_object()
        
        # Check permission
        if not IsGroupMember().has_object_permission(request, self, group):
            return Response(
                {"error": "You are not a member of this group"},
                status=status.HTTP_403_FORBIDDEN,
            )

        memberships = GroupMembership.objects.filter(
            group=group,
            is_active=True,
        ).select_related("user").order_by("-role", "joined_at")

        serializer = GroupMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["Groups"])
    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        """Leave a group."""
        group = self.get_object()

        # Owner cannot leave their own group
        if group.owner == request.user:
            return Response(
                {"error": "Owner cannot leave the group. Transfer ownership first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            membership = GroupMembership.objects.get(
                group=group,
                user=request.user,
                is_active=True,
            )
            membership.is_active = False
            membership.save()
            return Response({"success": True, "message": "Left the group"})
        except GroupMembership.DoesNotExist:
            return Response(
                {"error": "You are not a member of this group"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(tags=["Groups"])
    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        """Join a public group."""
        group = self.get_object()

        if not group.is_public:
            return Response(
                {"error": "This group is not public. You need an invitation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        membership, created = GroupMembership.objects.get_or_create(
            group=group,
            user=request.user,
            defaults={"role": GroupMembership.Role.MEMBER},
        )

        if not created:
            if membership.is_active:
                return Response(
                    {"error": "You are already a member"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            membership.is_active = True
            membership.save()

        return Response({
            "success": True,
            "message": "Joined the group",
            "membership_id": membership.id,
        })

    @extend_schema(tags=["Groups"], request=UpdateMembershipRoleSerializer)
    @action(detail=True, methods=["post"], url_path="members/(?P<user_id>[^/.]+)/role")
    def update_member_role(self, request, pk=None, user_id=None):
        """Update a member's role (admin only)."""
        group = self.get_object()

        # Check admin permission
        if not IsGroupAdmin().has_object_permission(request, self, group):
            return Response(
                {"error": "Only admins can change roles"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UpdateMembershipRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            membership = GroupMembership.objects.get(
                group=group,
                user_id=user_id,
                is_active=True,
            )
        except GroupMembership.DoesNotExist:
            return Response(
                {"error": "Member not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Cannot change owner's role
        if membership.user == group.owner:
            return Response(
                {"error": "Cannot change owner's role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.role = serializer.validated_data["role"]
        membership.save()

        return Response({
            "success": True,
            "message": f"Role updated to {membership.role}",
        })

    @extend_schema(tags=["Groups"])
    @action(detail=True, methods=["post"], url_path="members/(?P<user_id>[^/.]+)/remove")
    def remove_member(self, request, pk=None, user_id=None):
        """Remove a member from the group (admin only)."""
        group = self.get_object()

        # Check admin permission
        if not IsGroupAdmin().has_object_permission(request, self, group):
            return Response(
                {"error": "Only admins can remove members"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            membership = GroupMembership.objects.get(
                group=group,
                user_id=user_id,
                is_active=True,
            )
        except GroupMembership.DoesNotExist:
            return Response(
                {"error": "Member not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Cannot remove owner
        if membership.user == group.owner:
            return Response(
                {"error": "Cannot remove the owner"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.is_active = False
        membership.save()

        return Response({
            "success": True,
            "message": "Member removed",
        })


@extend_schema_view(
    list=extend_schema(tags=["Group Invitations"]),
    retrieve=extend_schema(tags=["Group Invitations"]),
    create=extend_schema(tags=["Group Invitations"]),
    destroy=extend_schema(tags=["Group Invitations"]),
)
class GroupInvitationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing group invitations.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = GroupInvitationSerializer
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        user = self.request.user
        # Show invitations user received or created
        return GroupInvitation.objects.filter(
            Q(invited_user=user) |
            Q(invited_email__iexact=user.email) |
            Q(invited_by=user)
        ).select_related("group", "invited_by", "invited_user").order_by("-created_at")

    @extend_schema(tags=["Group Invitations"], request=CreateInvitationSerializer)
    def create(self, request, *args, **kwargs):
        """Create a new invitation."""
        serializer = CreateInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group_id = request.data.get("group_id")
        if not group_id:
            return Response(
                {"error": "group_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = get_object_or_404(Group, id=group_id)

        # Check if user can invite
        if not CanInviteToGroup().has_object_permission(request, self, group):
            return Response(
                {"error": "You don't have permission to invite to this group"},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = serializer.validated_data
        
        # Get invited user if user_id provided
        invited_user = None
        if data.get("user_id"):
            invited_user = get_object_or_404(User, id=data["user_id"])

        # Check if user is already a member
        if invited_user:
            if GroupMembership.objects.filter(
                group=group, user=invited_user, is_active=True
            ).exists():
                return Response(
                    {"error": "User is already a member"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create invitation
        invitation = GroupInvitation.objects.create(
            group=group,
            invited_user=invited_user,
            invited_email=data.get("email", ""),
            invited_by=request.user,
            assigned_role=data.get("role", GroupMembership.Role.MEMBER),
            message=data.get("message", ""),
            expires_at=timezone.now() + timedelta(days=data.get("expires_days", 7)),
        )

        return Response(
            GroupInvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["Group Invitations"])
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """Accept an invitation."""
        invitation = self.get_object()

        # Check if user is the recipient
        if not IsInvitationRecipient().has_object_permission(request, self, invitation):
            return Response(
                {"error": "This invitation is not for you"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not invitation.is_valid:
            return Response(
                {"error": "Invitation is no longer valid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            membership = invitation.accept(request.user)
            return Response({
                "success": True,
                "message": f"Joined {invitation.group.name}",
                "membership_id": membership.id,
            })
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(tags=["Group Invitations"])
    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        """Decline an invitation."""
        invitation = self.get_object()

        # Check if user is the recipient
        if not IsInvitationRecipient().has_object_permission(request, self, invitation):
            return Response(
                {"error": "This invitation is not for you"},
                status=status.HTTP_403_FORBIDDEN,
            )

        invitation.decline()
        return Response({
            "success": True,
            "message": "Invitation declined",
        })

    def destroy(self, request, *args, **kwargs):
        """Cancel an invitation (only by creator or group admin)."""
        invitation = self.get_object()

        # Check if user created the invitation or is group admin
        if invitation.invited_by != request.user:
            if not IsGroupAdmin().has_object_permission(request, self, invitation.group):
                return Response(
                    {"error": "You can only cancel your own invitations"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        invitation.cancel()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Group Invitations"])
class AcceptInviteByCodeView(APIView):
    """
    Accept an invitation using invite code.
    
    This is used for link-based invitations.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invite_code = serializer.validated_data["invite_code"]

        try:
            invitation = GroupInvitation.objects.get(invite_code=invite_code)
        except GroupInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid invite code"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not invitation.is_valid:
            return Response(
                {"error": "Invitation is no longer valid or has expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            membership = invitation.accept(request.user)
            return Response({
                "success": True,
                "message": f"Joined {invitation.group.name}",
                "group_id": invitation.group.id,
                "membership_id": membership.id,
            })
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

