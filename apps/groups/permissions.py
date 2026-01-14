"""
Permissions for Groups app.

Defines who can perform actions on groups, memberships, and invitations.
"""

from rest_framework import permissions

from .models import Group, GroupMembership


class IsGroupOwner(permissions.BasePermission):
    """
    Permission check for group owner.
    
    Only the owner can:
    - Delete the group
    - Transfer ownership
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Group):
            return obj.owner == request.user
        if isinstance(obj, GroupMembership):
            return obj.group.owner == request.user
        return False


class IsGroupAdmin(permissions.BasePermission):
    """
    Permission check for group admin.
    
    Admins can:
    - Edit group settings
    - Manage members (invite, remove, change roles)
    - Manage invitations
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if isinstance(obj, Group):
            group = obj
        elif hasattr(obj, "group"):
            group = obj.group
        else:
            return False

        # Owner is always admin
        if group.owner == user:
            return True

        # Check membership role
        try:
            membership = GroupMembership.objects.get(
                group=group,
                user=user,
                is_active=True,
            )
            return membership.role == GroupMembership.Role.ADMIN
        except GroupMembership.DoesNotExist:
            return False


class IsGroupModerator(permissions.BasePermission):
    """
    Permission check for group moderator or above.
    
    Moderators can:
    - Invite new members (if allowed by group settings)
    - Remove regular members
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if isinstance(obj, Group):
            group = obj
        elif hasattr(obj, "group"):
            group = obj.group
        else:
            return False

        # Owner is always moderator+
        if group.owner == user:
            return True

        # Check membership role
        try:
            membership = GroupMembership.objects.get(
                group=group,
                user=user,
                is_active=True,
            )
            return membership.role in [
                GroupMembership.Role.ADMIN,
                GroupMembership.Role.MODERATOR,
            ]
        except GroupMembership.DoesNotExist:
            return False


class IsGroupMember(permissions.BasePermission):
    """
    Permission check for group member.
    
    Members can:
    - View group content
    - Leave the group
    - View other members
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if isinstance(obj, Group):
            group = obj
        elif hasattr(obj, "group"):
            group = obj.group
        else:
            return False

        # Owner is always member
        if group.owner == user:
            return True

        # Check active membership
        return GroupMembership.objects.filter(
            group=group,
            user=user,
            is_active=True,
        ).exists()


class CanInviteToGroup(permissions.BasePermission):
    """
    Permission check for inviting users to a group.
    
    Can invite if:
    - User is admin
    - User is moderator
    - Group allows member invites and user is member
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if isinstance(obj, Group):
            group = obj
        elif hasattr(obj, "group"):
            group = obj.group
        else:
            return False

        # Owner can always invite
        if group.owner == user:
            return True

        try:
            membership = GroupMembership.objects.get(
                group=group,
                user=user,
                is_active=True,
            )
            return membership.can_invite
        except GroupMembership.DoesNotExist:
            return False


class IsInvitationRecipient(permissions.BasePermission):
    """
    Permission check for invitation recipient.
    
    Only the invited user can accept/decline their invitation.
    """

    def has_object_permission(self, request, view, obj):
        # Check if user is the invited user
        if obj.invited_user == request.user:
            return True
        
        # Check if invitation was sent to user's email
        if obj.invited_email and obj.invited_email.lower() == request.user.email.lower():
            return True
        
        return False


# =============================================================================
# Helper functions for checking permissions in code
# =============================================================================


def user_is_group_member(user, group: Group) -> bool:
    """Check if user is an active member of the group."""
    if group.owner == user:
        return True
    return GroupMembership.objects.filter(
        group=group,
        user=user,
        is_active=True,
    ).exists()


def user_is_group_admin(user, group: Group) -> bool:
    """Check if user is admin of the group."""
    if group.owner == user:
        return True
    return GroupMembership.objects.filter(
        group=group,
        user=user,
        is_active=True,
        role=GroupMembership.Role.ADMIN,
    ).exists()


def user_can_invite_to_group(user, group: Group) -> bool:
    """Check if user can invite others to the group."""
    if group.owner == user:
        return True
    
    try:
        membership = GroupMembership.objects.get(
            group=group,
            user=user,
            is_active=True,
        )
        return membership.can_invite
    except GroupMembership.DoesNotExist:
        return False


def get_user_role_in_group(user, group: Group) -> str | None:
    """Get user's role in the group, or None if not a member."""
    if group.owner == user:
        return "owner"
    
    try:
        membership = GroupMembership.objects.get(
            group=group,
            user=user,
            is_active=True,
        )
        return membership.role
    except GroupMembership.DoesNotExist:
        return None


def get_visible_groups_for_user(user):
    """Get all groups visible to a user (member of or public)."""
    from django.db.models import Q
    
    return Group.objects.filter(
        Q(owner=user) |
        Q(memberships__user=user, memberships__is_active=True) |
        Q(is_public=True)
    ).distinct()

