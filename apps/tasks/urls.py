"""
URL configuration for the Tasks app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TaskCompletionViewSet, TaskGroupViewSet, TaskViewSet

app_name = "tasks"

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="task")
router.register("task-groups", TaskGroupViewSet, basename="task-group")
router.register("completions", TaskCompletionViewSet, basename="completion")

urlpatterns = [
    path("", include(router.urls)),
]
