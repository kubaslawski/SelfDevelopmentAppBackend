"""
Views for the Feedback app.
"""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Feedback
from .serializers import (
    FeedbackCreateSerializer,
    FeedbackSerializer,
    FeedbackListSerializer,
    FeedbackAdminSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Feedback"]),
    create=extend_schema(tags=["Feedback"]),
    retrieve=extend_schema(tags=["Feedback"]),
    types=extend_schema(tags=["Feedback"]),
)
class FeedbackViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for user feedback.

    Users can:
    - Create new feedback (POST /feedback/)
    - List their own feedback (GET /feedback/)
    - View details of their own feedback (GET /feedback/{id}/)

    Admin can access all feedback via Django admin panel.
    """

    queryset = Feedback.objects.none()  # For schema generation
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["feedback_type", "status"]
    lookup_value_regex = r"\d+"  # Ensure path parameter is typed as integer

    def get_queryset(self):
        """Return only the current user's feedback."""
        # Check for schema generation
        if getattr(self, "swagger_fake_view", False):
            return Feedback.objects.none()
        return Feedback.objects.filter(user=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return FeedbackCreateSerializer
        if self.action == "list":
            return FeedbackListSerializer
        return FeedbackSerializer

    @action(detail=False, methods=["get"])
    def types(self, request):
        """
        Get available feedback types.
        Useful for populating dropdown/picker in the app.
        """
        types = [
            {"value": choice[0], "label": choice[1]}
            for choice in Feedback.FeedbackType.choices
        ]
        return Response(types, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(tags=["Admin Feedback"]),
    create=extend_schema(tags=["Admin Feedback"]),
    retrieve=extend_schema(tags=["Admin Feedback"]),
    update=extend_schema(tags=["Admin Feedback"]),
    partial_update=extend_schema(tags=["Admin Feedback"]),
    destroy=extend_schema(tags=["Admin Feedback"]),
    resolve=extend_schema(tags=["Admin Feedback"]),
)
class AdminFeedbackViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing all feedback.
    Only accessible by staff users.
    """

    queryset = Feedback.objects.all().order_by("-created_at")
    serializer_class = FeedbackAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["feedback_type", "status", "priority", "user"]

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Mark feedback as resolved."""
        feedback = self.get_object()
        feedback.mark_resolved()
        serializer = self.get_serializer(feedback)
        return Response(serializer.data, status=status.HTTP_200_OK)

