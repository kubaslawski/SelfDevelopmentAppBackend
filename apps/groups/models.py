"""
Group models for collaborative task/goal management.

Supports:
- Private/Public/Group visibility for tasks and goals
- Group creation with admin roles
- Invitations system
- Role-based permissions within groups
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Abstract base model with timestamps."""

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True


class Group(TimeStampedModel):
    """
    A group for sharing tasks and goals.
    
    Groups allow users to collaborate on tasks and goals with
    configurable visibility and permissions.
    """

    name = models.CharField(
        _("name"),
        max_length=100,
        help_text=_("Group display name"),
    )
    description = models.TextField(
        _("description"),
        blank=True,
        default="",
        help_text=_("Group description"),
    )
    slug = models.SlugField(
        _("slug"),
        max_length=100,
        unique=True,
        help_text=_("Unique URL-friendly identifier"),
    )
    
    # Group settings
    is_public = models.BooleanField(
        _("is public"),
        default=False,
        help_text=_("Public groups can be discovered and joined by anyone"),
    )
    allow_member_invites = models.BooleanField(
        _("allow member invites"),
        default=False,
        help_text=_("Allow non-admin members to invite others"),
    )
    
    # Owner (creator) - always has full permissions
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_groups",
        verbose_name=_("owner"),
    )
    
    # Optional: group avatar/icon
    icon = models.CharField(
        _("icon"),
        max_length=10,
        default="👥",
        help_text=_("Emoji icon for the group"),
    )
    color = models.CharField(
        _("color"),
        max_length=7,
        default="#6366F1",
        help_text=_("Hex color for the group"),
    )

    class Meta:
        verbose_name = _("group")
        verbose_name_plural = _("groups")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate slug if not set
        if not self.slug:
            base_slug = self.name.lower().replace(" ", "-")[:50]
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    @property
    def member_count(self) -> int:
        """Number of members in the group."""
        return self.memberships.filter(is_active=True).count()

    @property
    def admin_count(self) -> int:
        """Number of admins in the group."""
        return self.memberships.filter(is_active=True, role=GroupMembership.Role.ADMIN).count()


class GroupMembership(TimeStampedModel):
    """
    Membership record for a user in a group.
    
    Tracks role, permissions, and membership status.
    """

    class Role(models.TextChoices):
        """Membership roles with different permission levels."""
        
        MEMBER = "member", _("Member")
        MODERATOR = "moderator", _("Moderator")
        ADMIN = "admin", _("Admin")

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("group"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships",
        verbose_name=_("user"),
    )
    
    # Role and status
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    is_active = models.BooleanField(
        _("is active"),
        default=True,
        help_text=_("Inactive memberships are soft-deleted"),
    )
    
    # Timestamps
    joined_at = models.DateTimeField(
        _("joined at"),
        auto_now_add=True,
    )
    
    # Who invited this member
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
        verbose_name=_("invited by"),
    )

    class Meta:
        verbose_name = _("group membership")
        verbose_name_plural = _("group memberships")
        unique_together = ["group", "user"]
        ordering = ["-joined_at"]

    def __str__(self) -> str:
        return f"{self.user} in {self.group} ({self.role})"

    @property
    def is_admin(self) -> bool:
        """Check if user is admin of the group."""
        return self.role == self.Role.ADMIN or self.user == self.group.owner

    @property
    def is_moderator_or_above(self) -> bool:
        """Check if user is moderator or admin."""
        return self.role in [self.Role.ADMIN, self.Role.MODERATOR] or self.user == self.group.owner

    @property
    def can_invite(self) -> bool:
        """Check if user can invite others."""
        if self.is_admin:
            return True
        if self.group.allow_member_invites:
            return True
        return self.role == self.Role.MODERATOR


class GroupInvitation(TimeStampedModel):
    """
    Invitation to join a group.
    
    Can be sent to existing users (by email) or generate
    a shareable invite link.
    """

    class Status(models.TextChoices):
        """Invitation status."""
        
        PENDING = "pending", _("Pending")
        ACCEPTED = "accepted", _("Accepted")
        DECLINED = "declined", _("Declined")
        EXPIRED = "expired", _("Expired")
        CANCELLED = "cancelled", _("Cancelled")

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name=_("group"),
    )
    
    # Invitation target - either specific user or email
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="received_invitations",
        verbose_name=_("invited user"),
    )
    invited_email = models.EmailField(
        _("invited email"),
        blank=True,
        default="",
        help_text=_("Email address if inviting non-registered user"),
    )
    
    # Invitation details
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_invitations",
        verbose_name=_("invited by"),
    )
    
    # Invite code for link-based invitations
    invite_code = models.CharField(
        _("invite code"),
        max_length=32,
        unique=True,
        help_text=_("Unique code for invite link"),
    )
    
    # Role to assign when accepted
    assigned_role = models.CharField(
        _("assigned role"),
        max_length=20,
        choices=GroupMembership.Role.choices,
        default=GroupMembership.Role.MEMBER,
    )
    
    # Status and expiration
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    expires_at = models.DateTimeField(
        _("expires at"),
        help_text=_("When this invitation expires"),
    )
    
    # Optional message
    message = models.TextField(
        _("message"),
        blank=True,
        default="",
        help_text=_("Optional invitation message"),
    )

    class Meta:
        verbose_name = _("group invitation")
        verbose_name_plural = _("group invitations")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["invite_code"]),
            models.Index(fields=["invited_email"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self) -> str:
        target = self.invited_user or self.invited_email or "anyone"
        return f"Invitation to {self.group} for {target}"

    def save(self, *args, **kwargs):
        # Auto-generate invite code if not set
        if not self.invite_code:
            self.invite_code = uuid.uuid4().hex
        # Set default expiration (7 days)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if invitation can still be accepted."""
        return self.status == self.Status.PENDING and not self.is_expired

    def accept(self, user) -> GroupMembership:
        """
        Accept the invitation and create membership.
        
        Returns the created GroupMembership.
        """
        if not self.is_valid:
            raise ValueError("Invitation is no longer valid")

        # Create membership
        membership, created = GroupMembership.objects.get_or_create(
            group=self.group,
            user=user,
            defaults={
                "role": self.assigned_role,
                "invited_by": self.invited_by,
            },
        )

        if not created:
            # Reactivate if was inactive
            membership.is_active = True
            membership.save()

        # Update invitation status
        self.status = self.Status.ACCEPTED
        self.save()

        return membership

    def decline(self):
        """Decline the invitation."""
        self.status = self.Status.DECLINED
        self.save()

    def cancel(self):
        """Cancel the invitation (by inviter)."""
        self.status = self.Status.CANCELLED
        self.save()


# =============================================================================
# Visibility Mixin for Task/Goal models
# =============================================================================


class VisibilityMixin(models.Model):
    """
    Mixin to add visibility settings to Task/Goal models.
    
    Provides:
    - visibility: private/public/group
    - shared_with_groups: M2M relation to groups
    """

    class Visibility(models.TextChoices):
        """Visibility levels for content."""
        
        PRIVATE = "private", _("Private")
        GROUP = "group", _("Group")
        PUBLIC = "public", _("Public")

    visibility = models.CharField(
        _("visibility"),
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
        help_text=_("Who can see this item"),
    )
    
    shared_with_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="%(class)s_items",
        verbose_name=_("shared with groups"),
        help_text=_("Groups this item is shared with (when visibility is 'group')"),
    )

    class Meta:
        abstract = True

    def is_visible_to(self, user) -> bool:
        """Check if this item is visible to a specific user."""
        # Owner always sees their own items
        if hasattr(self, "user") and self.user == user:
            return True

        # Public items are visible to everyone
        if self.visibility == self.Visibility.PUBLIC:
            return True

        # Private items are only visible to owner
        if self.visibility == self.Visibility.PRIVATE:
            return False

        # Group items - check if user is member of any shared group
        if self.visibility == self.Visibility.GROUP:
            return self.shared_with_groups.filter(
                memberships__user=user,
                memberships__is_active=True,
            ).exists()

        return False

