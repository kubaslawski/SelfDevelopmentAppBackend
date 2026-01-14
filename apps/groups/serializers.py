"""
Serializers for Groups app.
"""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Group, GroupInvitation, GroupMembership
from .permissions import get_user_role_in_group

User = get_user_model()


# =============================================================================
# User serializers (nested)
# =============================================================================


class GroupUserSerializer(serializers.ModelSerializer):
    """Minimal user serializer for group context."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name"]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField())
    def get_full_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email


# =============================================================================
# Group serializers
# =============================================================================


class GroupListSerializer(serializers.ModelSerializer):
    """Serializer for group list view."""

    member_count = serializers.IntegerField(read_only=True)
    is_member = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "color",
            "is_public",
            "member_count",
            "is_member",
            "user_role",
            "created_at",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.BooleanField())
    def get_is_member(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            return False
        user = request.user
        if obj.owner == user:
            return True
        return GroupMembership.objects.filter(
            group=obj, user=user, is_active=True
        ).exists()

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_user_role(self, obj) -> str | None:
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            return None
        return get_user_role_in_group(request.user, obj)


class GroupDetailSerializer(serializers.ModelSerializer):
    """Serializer for group detail view."""

    owner = GroupUserSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    admin_count = serializers.IntegerField(read_only=True)
    is_member = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_invite = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "color",
            "is_public",
            "allow_member_invites",
            "owner",
            "member_count",
            "admin_count",
            "is_member",
            "user_role",
            "can_edit",
            "can_invite",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "owner",
            "member_count",
            "admin_count",
            "is_member",
            "user_role",
            "can_edit",
            "can_invite",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.BooleanField())
    def get_is_member(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            return False
        user = request.user
        if obj.owner == user:
            return True
        return GroupMembership.objects.filter(
            group=obj, user=user, is_active=True
        ).exists()

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_user_role(self, obj) -> str | None:
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            return None
        return get_user_role_in_group(request.user, obj)

    @extend_schema_field(serializers.BooleanField())
    def get_can_edit(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            return False
        role = get_user_role_in_group(request.user, obj)
        return role in ["owner", "admin"]

    @extend_schema_field(serializers.BooleanField())
    def get_can_invite(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            return False
        user = request.user
        if obj.owner == user:
            return True
        try:
            membership = GroupMembership.objects.get(
                group=obj, user=user, is_active=True
            )
            return membership.can_invite
        except GroupMembership.DoesNotExist:
            return False


class GroupCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new group."""

    class Meta:
        model = Group
        fields = [
            "name",
            "description",
            "icon",
            "color",
            "is_public",
            "allow_member_invites",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        group = Group.objects.create(owner=user, **validated_data)
        
        # Create admin membership for owner
        GroupMembership.objects.create(
            group=group,
            user=user,
            role=GroupMembership.Role.ADMIN,
        )
        
        return group


# =============================================================================
# Membership serializers
# =============================================================================


class GroupMembershipSerializer(serializers.ModelSerializer):
    """Serializer for group membership."""

    user = GroupUserSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = GroupMembership
        fields = [
            "id",
            "user",
            "role",
            "is_owner",
            "is_active",
            "joined_at",
            "created_at",
        ]
        read_only_fields = ["id", "user", "is_owner", "is_active", "joined_at", "created_at"]

    @extend_schema_field(serializers.BooleanField())
    def get_is_owner(self, obj) -> bool:
        return obj.user == obj.group.owner


class UpdateMembershipRoleSerializer(serializers.Serializer):
    """Serializer for updating a member's role."""

    role = serializers.ChoiceField(choices=GroupMembership.Role.choices)


# =============================================================================
# Invitation serializers
# =============================================================================


class GroupInvitationSerializer(serializers.ModelSerializer):
    """Serializer for group invitations."""

    invited_by = GroupUserSerializer(read_only=True)
    invited_user = GroupUserSerializer(read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = GroupInvitation
        fields = [
            "id",
            "group",
            "group_name",
            "invited_user",
            "invited_email",
            "invited_by",
            "assigned_role",
            "status",
            "message",
            "invite_code",
            "is_valid",
            "is_expired",
            "expires_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "group",
            "group_name",
            "invited_by",
            "status",
            "invite_code",
            "is_valid",
            "is_expired",
            "created_at",
        ]


class CreateInvitationSerializer(serializers.Serializer):
    """Serializer for creating an invitation."""

    group_id = serializers.IntegerField()
    email = serializers.EmailField(required=False, allow_blank=True)
    user_id = serializers.IntegerField(required=False, allow_null=True)
    role = serializers.ChoiceField(
        choices=GroupMembership.Role.choices,
        default=GroupMembership.Role.MEMBER,
    )
    message = serializers.CharField(required=False, allow_blank=True, default="")
    expires_days = serializers.IntegerField(default=7, min_value=1, max_value=30)

    def validate(self, data):
        if not data.get("email") and not data.get("user_id"):
            raise serializers.ValidationError(
                "Either 'email' or 'user_id' must be provided"
            )
        return data


class AcceptInvitationSerializer(serializers.Serializer):
    """Serializer for accepting an invitation."""

    invite_code = serializers.CharField(max_length=32)


# =============================================================================
# Response serializers for OpenAPI schema
# =============================================================================


class GroupActionResponseSerializer(serializers.Serializer):
    """Response serializer for group actions (join, leave, etc.)."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    membership_id = serializers.IntegerField(required=False)
    group_id = serializers.IntegerField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Response serializer for errors."""

    error = serializers.CharField()
