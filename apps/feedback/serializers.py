"""
Serializers for the Feedback app.
"""

from rest_framework import serializers

from .models import Feedback


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new feedback.
    Users can only set: feedback_type, title, message, app_version, device_info, screen_name
    """

    class Meta:
        model = Feedback
        fields = [
            "feedback_type",
            "title",
            "message",
            "app_version",
            "device_info",
            "screen_name",
        ]

    def create(self, validated_data):
        """Set the user from the request context."""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class FeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing feedback (user's own feedback).
    """

    feedback_type_display = serializers.CharField(
        source="get_feedback_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Feedback
        fields = [
            "id",
            "feedback_type",
            "feedback_type_display",
            "title",
            "message",
            "app_version",
            "device_info",
            "screen_name",
            "status",
            "status_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "status_display",
            "created_at",
            "updated_at",
        ]


class FeedbackListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing user's feedback.
    """

    feedback_type_display = serializers.CharField(
        source="get_feedback_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Feedback
        fields = [
            "id",
            "feedback_type",
            "feedback_type_display",
            "title",
            "status",
            "status_display",
            "created_at",
        ]


class FeedbackAdminSerializer(serializers.ModelSerializer):
    """
    Full serializer for admin use - includes all fields.
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)
    feedback_type_display = serializers.CharField(
        source="get_feedback_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )

    class Meta:
        model = Feedback
        fields = [
            "id",
            "user",
            "user_email",
            "feedback_type",
            "feedback_type_display",
            "title",
            "message",
            "app_version",
            "device_info",
            "screen_name",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "admin_notes",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "user_email", "created_at", "updated_at"]


