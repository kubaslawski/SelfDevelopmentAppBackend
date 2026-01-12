"""
URL configuration for the Feedback app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FeedbackViewSet, AdminFeedbackViewSet

router = DefaultRouter()
router.register(r"feedback", FeedbackViewSet, basename="feedback")
router.register(r"admin/feedback", AdminFeedbackViewSet, basename="admin-feedback")

urlpatterns = [
    path("", include(router.urls)),
]

