"""Admin configuration for Groups app."""

from django.contrib import admin

from .models import Group, GroupInvitation, GroupMembership


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    readonly_fields = ["joined_at", "created_at"]
    raw_id_fields = ["user", "invited_by"]


class GroupInvitationInline(admin.TabularInline):
    model = GroupInvitation
    extra = 0
    readonly_fields = ["invite_code", "created_at"]
    raw_id_fields = ["invited_user", "invited_by"]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "owner", "is_public", "member_count", "created_at"]
    list_filter = ["is_public", "created_at"]
    search_fields = ["name", "slug", "owner__email"]
    readonly_fields = ["slug", "created_at", "updated_at"]
    raw_id_fields = ["owner"]
    inlines = [GroupMembershipInline, GroupInvitationInline]

    fieldsets = (
        (None, {
            "fields": ("name", "slug", "description", "owner"),
        }),
        ("Settings", {
            "fields": ("is_public", "allow_member_invites", "icon", "color"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "group", "role", "is_active", "joined_at"]
    list_filter = ["role", "is_active", "joined_at"]
    search_fields = ["user__email", "group__name"]
    raw_id_fields = ["user", "group", "invited_by"]
    readonly_fields = ["joined_at", "created_at", "updated_at"]


@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):
    list_display = [
        "group",
        "invited_user",
        "invited_email",
        "status",
        "assigned_role",
        "expires_at",
    ]
    list_filter = ["status", "assigned_role", "created_at"]
    search_fields = ["group__name", "invited_user__email", "invited_email"]
    raw_id_fields = ["group", "invited_user", "invited_by"]
    readonly_fields = ["invite_code", "created_at", "updated_at"]

