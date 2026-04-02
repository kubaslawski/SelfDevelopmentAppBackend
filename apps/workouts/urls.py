from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ExerciseProgressAPIView,
    ExerciseSetViewSet,
    ExerciseViewSet,
    SessionExerciseViewSet,
    WorkoutPlanViewSet,
    WorkoutSessionViewSet,
)

app_name = "workouts"

router = DefaultRouter()
router.register(r"workouts/plans", WorkoutPlanViewSet, basename="workout-plan")
router.register(r"workouts/exercises", ExerciseViewSet, basename="exercise")
router.register(r"workouts/sessions", WorkoutSessionViewSet, basename="workout-session")
router.register(r"workouts/session-exercises", SessionExerciseViewSet, basename="session-exercise")
router.register(r"workouts/sets", ExerciseSetViewSet, basename="exercise-set")

urlpatterns = [
    path("", include(router.urls)),
    path("workouts/progress/", ExerciseProgressAPIView.as_view(), name="exercise-progress"),
]
