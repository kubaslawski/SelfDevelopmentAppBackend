"""Views for Notifications app."""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationPreference
from .serializers import (
    NotificationListSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
    RegisterPushTokenSerializer,
)
from .services import get_or_create_preferences


class NotificationPreferenceView(APIView):
    """
    View for managing notification preferences.

    GET: Get current user's notification preferences
    PUT/PATCH: Update notification preferences
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        responses={200: NotificationPreferenceSerializer},
    )
    def get(self, request):
        """Get notification preferences."""
        prefs = get_or_create_preferences(request.user)
        serializer = NotificationPreferenceSerializer(prefs)
        return Response(serializer.data)

    @extend_schema(
        tags=["Notifications"],
        request=NotificationPreferenceSerializer,
        responses={200: NotificationPreferenceSerializer},
    )
    def put(self, request):
        """Update notification preferences."""
        prefs = get_or_create_preferences(request.user)
        serializer = NotificationPreferenceSerializer(prefs, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        tags=["Notifications"],
        request=NotificationPreferenceSerializer,
        responses={200: NotificationPreferenceSerializer},
    )
    def patch(self, request):
        """Partially update notification preferences."""
        prefs = get_or_create_preferences(request.user)
        serializer = NotificationPreferenceSerializer(
            prefs, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RegisterPushTokenView(APIView):
    """
    Register or update push notification token.

    POST: Register a new push token for the current user
    DELETE: Remove push token (disable push notifications)
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        request=RegisterPushTokenSerializer,
        responses={200: None},
    )
    def post(self, request):
        """Register push token."""
        serializer = RegisterPushTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prefs = get_or_create_preferences(request.user)
        prefs.push_token = serializer.validated_data["push_token"]
        prefs.save(update_fields=["push_token", "updated_at"])

        return Response(
            {
                "success": True,
                "message": "Push token registered successfully.",
            }
        )

    @extend_schema(
        tags=["Notifications"],
        responses={200: None},
    )
    def delete(self, request):
        """Remove push token."""
        prefs = get_or_create_preferences(request.user)
        prefs.push_token = ""
        prefs.save(update_fields=["push_token", "updated_at"])

        return Response(
            {
                "success": True,
                "message": "Push token removed.",
            }
        )


@extend_schema_view(
    list=extend_schema(tags=["Notifications"]),
    retrieve=extend_schema(tags=["Notifications"]),
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notifications.

    Read-only - notifications are created by the system.
    Users can view their notifications and mark them as read.
    """

    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.none()  # Default for schema generation

    def get_queryset(self):
        """Filter notifications to current user."""
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user).select_related(
            "task"
        )

    def get_serializer_class(self):
        """Use list serializer for list action."""
        if self.action == "list":
            return NotificationListSerializer
        return NotificationSerializer

    @extend_schema(tags=["Notifications"])
    @action(detail=False, methods=["get"])
    def pending(self, request):
        """Get pending notifications for the user."""
        notifications = self.get_queryset().filter(
            status=Notification.Status.PENDING
        )
        serializer = NotificationListSerializer(notifications, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["Notifications"])
    @action(detail=False, methods=["get"])
    def history(self, request):
        """Get sent notifications history."""
        notifications = self.get_queryset().filter(
            status=Notification.Status.SENT
        ).order_by("-sent_at")[:50]
        serializer = NotificationListSerializer(notifications, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["Notifications"])
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a pending notification."""
        notification = self.get_object()

        if notification.status != Notification.Status.PENDING:
            return Response(
                {
                    "success": False,
                    "error": "invalid_status",
                    "message": "Can only cancel pending notifications.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification.cancel()
        return Response(
            {
                "success": True,
                "message": "Notification cancelled.",
            }
        )

