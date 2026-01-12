"""
Admin configuration for the Feedback app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Admin configuration for Feedback model."""

    list_display = [
        "id",
        "colored_type",
        "title",
        "user_email",
        "colored_status",
        "priority",
        "created_at",
    ]
    list_filter = ["feedback_type", "status", "priority", "created_at"]
    search_fields = ["title", "message", "user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["created_at", "updated_at", "resolved_at"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Feedback Content",
            {
                "fields": ("user", "feedback_type", "title", "message"),
            },
        ),
        (
            "App Context",
            {
                "fields": ("app_version", "device_info", "screen_name"),
                "classes": ("collapse",),
            },
        ),
        (
            "Status & Management",
            {
                "fields": ("status", "priority", "admin_notes", "resolved_at"),
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

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User"

    def colored_type(self, obj):
        colors = {
            "bug_report": "#EF4444",  # red
            "suggestion": "#22C55E",  # green
            "comment": "#3B82F6",  # blue
            "question": "#F59E0B",  # amber
        }
        color = colors.get(obj.feedback_type, "#6B7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_feedback_type_display(),
        )

    colored_type.short_description = "Type"

    def colored_status(self, obj):
        colors = {
            "new": "#8B5CF6",  # purple
            "in_review": "#3B82F6",  # blue
            "in_progress": "#F59E0B",  # amber
            "resolved": "#22C55E",  # green
            "closed": "#6B7280",  # gray
            "wont_fix": "#EF4444",  # red
        }
        color = colors.get(obj.status, "#6B7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    colored_status.short_description = "Status"

    actions = ["mark_as_resolved", "mark_as_in_review"]

    @admin.action(description="Mark selected as Resolved")
    def mark_as_resolved(self, request, queryset):
        for feedback in queryset:
            feedback.mark_resolved()
        self.message_user(request, f"{queryset.count()} feedback(s) marked as resolved.")

    @admin.action(description="Mark selected as In Review")
    def mark_as_in_review(self, request, queryset):
        queryset.update(status=Feedback.Status.IN_REVIEW)
        self.message_user(request, f"{queryset.count()} feedback(s) marked as in review.")

