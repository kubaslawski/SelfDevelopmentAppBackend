"""URL configuration for Groups app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AcceptInviteByCodeView, GroupInvitationViewSet, GroupViewSet

app_name = "groups"

router = DefaultRouter()
router.register("groups", GroupViewSet, basename="group")
router.register("invitations", GroupInvitationViewSet, basename="invitation")

urlpatterns = [
    path("invitations/accept-by-code/", AcceptInviteByCodeView.as_view(), name="accept-by-code"),
    path("", include(router.urls)),
]

