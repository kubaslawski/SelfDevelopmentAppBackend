"""Serializers for Notifications app."""

from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference."""

    class Meta:
        model = NotificationPreference
        fields = [
            "notifications_enabled",
            "push_enabled",
            "email_enabled",
            "regular_task_reminders",
            "daily_reminder_enabled",
            "daily_reminder_hours_before",
            "quiet_hours_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
            "push_token",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class RegisterPushTokenSerializer(serializers.Serializer):
    """Serializer for registering push notification token."""

    push_token = serializers.CharField(
        max_length=512,
        help_text="Expo push notification token",
    )


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification."""

    task_title = serializers.CharField(source="task.title", read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "body",
            "scheduled_for",
            "status",
            "sent_at",
            "task",
            "task_title",
            "created_at",
        ]
        read_only_fields = fields


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing notifications."""

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "status",
            "scheduled_for",
            "task",
        ]

