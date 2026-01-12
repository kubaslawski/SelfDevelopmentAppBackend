"""
URL configuration for Goals API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GoalViewSet, MilestoneViewSet

router = DefaultRouter()
router.register(r"goals", GoalViewSet, basename="goal")
router.register(r"milestones", MilestoneViewSet, basename="milestone")

urlpatterns = [
    path("", include(router.urls)),
]

