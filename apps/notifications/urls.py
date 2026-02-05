"""URL configuration for Notifications app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MotivationalQuotesView,
    NotificationPreferenceView,
    NotificationViewSet,
    RegisterPushTokenView,
)

app_name = "notifications"

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("notifications/preferences/", NotificationPreferenceView.as_view(), name="preferences"),
    path("notifications/push-token/", RegisterPushTokenView.as_view(), name="push-token"),
    path("notifications/motivational-quotes/", MotivationalQuotesView.as_view(), name="motivational-quotes"),
    path("", include(router.urls)),
]

