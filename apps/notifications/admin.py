"""Admin configuration for Notifications app."""

from django.contrib import admin
from django.utils.html import format_html

from .models import Notification, NotificationPreference


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin for NotificationPreference."""

    list_display = [
        "user",
        "notifications_enabled",
        "push_enabled",
        "email_enabled",
        "daily_reminder_enabled",
        "quiet_hours_display",
        "has_push_token",
    ]
    list_filter = [
        "notifications_enabled",
        "push_enabled",
        "email_enabled",
        "daily_reminder_enabled",
        "quiet_hours_enabled",
    ]
    search_fields = ["user__email", "user__username"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "User",
            {
                "fields": ("user",),
            },
        ),
        (
            "Global Settings",
            {
                "fields": (
                    "notifications_enabled",
                    "push_enabled",
                    "email_enabled",
                ),
            },
        ),
        (
            "Task Reminders",
            {
                "fields": (
                    "regular_task_reminders",
                    "daily_reminder_enabled",
                    "daily_reminder_hours_before",
                ),
            },
        ),
        (
            "Quiet Hours",
            {
                "fields": (
                    "quiet_hours_enabled",
                    "quiet_hours_start",
                    "quiet_hours_end",
                ),
            },
        ),
        (
            "Push Token",
            {
                "fields": ("push_token",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def quiet_hours_display(self, obj):
        """Display quiet hours range."""
        if obj.quiet_hours_enabled:
            return f"{obj.quiet_hours_start} - {obj.quiet_hours_end}"
        return "-"

    quiet_hours_display.short_description = "Quiet Hours"

    def has_push_token(self, obj):
        """Display if user has push token."""
        if obj.push_token:
            return format_html(
                '<span style="color: green;">✓</span>'
            )
        return format_html(
            '<span style="color: gray;">✗</span>'
        )

    has_push_token.short_description = "Push Token"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for Notification."""

    list_display = [
        "id",
        "user",
        "notification_type",
        "title_preview",
        "status_badge",
        "scheduled_for",
        "sent_at",
        "task_link",
    ]
    list_filter = [
        "notification_type",
        "status",
        "sent_via_push",
        "sent_via_email",
        "created_at",
        "scheduled_for",
    ]
    search_fields = ["user__email", "title", "body", "task__title"]
    ordering = ["-scheduled_for"]
    readonly_fields = ["created_at", "updated_at", "sent_at"]
    date_hierarchy = "scheduled_for"
    raw_id_fields = ["user", "task"]

    fieldsets = (
        (
            "User & Task",
            {
                "fields": ("user", "task"),
            },
        ),
        (
            "Notification Content",
            {
                "fields": (
                    "notification_type",
                    "title",
                    "body",
                ),
            },
        ),
        (
            "Scheduling",
            {
                "fields": (
                    "scheduled_for",
                    "reminder_key",
                ),
            },
        ),
        (
            "Delivery Status",
            {
                "fields": (
                    "status",
                    "sent_at",
                    "sent_via_push",
                    "sent_via_email",
                    "error_message",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def title_preview(self, obj):
        """Display truncated title."""
        if len(obj.title) > 40:
            return f"{obj.title[:40]}..."
        return obj.title

    title_preview.short_description = "Title"

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            "pending": "#ffc107",
            "scheduled": "#17a2b8",
            "sent": "#28a745",
            "failed": "#dc3545",
            "cancelled": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def task_link(self, obj):
        """Display task as link."""
        if obj.task:
            return obj.task.title[:30]
        return "-"

    task_link.short_description = "Task"

    actions = ["mark_as_cancelled", "resend_notification"]

    @admin.action(description="Cancel selected notifications")
    def mark_as_cancelled(self, request, queryset):
        count = queryset.filter(status=Notification.Status.PENDING).update(
            status=Notification.Status.CANCELLED
        )
        self.message_user(request, f"Cancelled {count} notifications.")

    @admin.action(description="Resend failed notifications")
    def resend_notification(self, request, queryset):
        count = queryset.filter(status=Notification.Status.FAILED).update(
            status=Notification.Status.PENDING
        )
        self.message_user(request, f"Rescheduled {count} notifications for resend.")


