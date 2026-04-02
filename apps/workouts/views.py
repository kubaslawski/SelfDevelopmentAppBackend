from django.db.models.functions import TruncDate
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Exercise, ExerciseSet, SessionExercise, WorkoutPlan, WorkoutSession
from .serializers import (
    ExerciseSerializer,
    ExerciseSetSerializer,
    SessionExerciseSerializer,
    WorkoutPlanSerializer,
    WorkoutSessionSerializer,
)
from .services.progress_service import get_exercise_progress


@extend_schema_view(
    list=extend_schema(tags=["Workouts"]),
    create=extend_schema(tags=["Workouts"]),
    retrieve=extend_schema(tags=["Workouts"]),
    update=extend_schema(tags=["Workouts"]),
    partial_update=extend_schema(tags=["Workouts"]),
    destroy=extend_schema(tags=["Workouts"]),
    last_session=extend_schema(tags=["Workouts"]),
)
class WorkoutPlanViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WorkoutPlan.objects.none()
        return WorkoutPlan.objects.filter(user=self.request.user).prefetch_related(
            "plan_exercises__exercise"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"], url_path="last-session")
    def last_session(self, request, pk=None):
        plan = self.get_object()
        session = (
            plan.sessions.select_related("workout_plan")
            .prefetch_related("session_exercises__exercise", "session_exercises__exercise_sets")
            .order_by("-started_at")
            .first()
        )
        if not session:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = WorkoutSessionSerializer(session)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=["Workouts"]),
    create=extend_schema(tags=["Workouts"]),
    retrieve=extend_schema(tags=["Workouts"]),
    update=extend_schema(tags=["Workouts"]),
    partial_update=extend_schema(tags=["Workouts"]),
    destroy=extend_schema(tags=["Workouts"]),
    history=extend_schema(tags=["Workouts"]),
)
class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        exercise = self.get_object()
        history_qs = (
            ExerciseSet.objects.filter(
                session_exercise__exercise=exercise,
                session_exercise__session__user=request.user,
            )
            .annotate(date=TruncDate("created_at"))
            .values("date", "reps", "weight")
            .order_by("-created_at")
        )
        return Response(history_qs)


@extend_schema_view(
    list=extend_schema(tags=["Workouts"]),
    create=extend_schema(tags=["Workouts"]),
    retrieve=extend_schema(tags=["Workouts"]),
    update=extend_schema(tags=["Workouts"]),
    partial_update=extend_schema(tags=["Workouts"]),
    destroy=extend_schema(tags=["Workouts"]),
)
class WorkoutSessionViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WorkoutSession.objects.none()
        return (
            WorkoutSession.objects.filter(user=self.request.user)
            .select_related("workout_plan")
            .prefetch_related("session_exercises__exercise", "session_exercises__exercise_sets")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema_view(
    list=extend_schema(tags=["Workouts"]),
    create=extend_schema(tags=["Workouts"]),
    retrieve=extend_schema(tags=["Workouts"]),
    update=extend_schema(tags=["Workouts"]),
    partial_update=extend_schema(tags=["Workouts"]),
    destroy=extend_schema(tags=["Workouts"]),
)
class SessionExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = SessionExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SessionExercise.objects.none()
        return (
            SessionExercise.objects.filter(session__user=self.request.user)
            .select_related("session", "exercise")
            .prefetch_related("exercise_sets")
        )

    def perform_create(self, serializer):
        session = serializer.validated_data.get("session")
        if session.user_id != self.request.user.id:
            raise PermissionDenied("Cannot create session exercise for another user.")
        serializer.save()


@extend_schema_view(
    list=extend_schema(tags=["Workouts"]),
    create=extend_schema(tags=["Workouts"]),
    retrieve=extend_schema(tags=["Workouts"]),
    update=extend_schema(tags=["Workouts"]),
    partial_update=extend_schema(tags=["Workouts"]),
    destroy=extend_schema(tags=["Workouts"]),
)
class ExerciseSetViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ExerciseSet.objects.none()
        return ExerciseSet.objects.filter(
            session_exercise__session__user=self.request.user
        ).select_related("session_exercise", "session_exercise__exercise")

    def perform_create(self, serializer):
        session_exercise = serializer.validated_data.get("session_exercise")
        if session_exercise.session.user_id != self.request.user.id:
            raise PermissionDenied("Cannot create set for another user session.")
        serializer.save()


class ExerciseProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Workouts"])
    def get(self, request):
        exercise_id = request.query_params.get("exercise_id")
        if not exercise_id:
            return Response(
                {"detail": "exercise_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            exercise_id_int = int(exercise_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "exercise_id must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_from_raw = request.query_params.get("from")
        date_to_raw = request.query_params.get("to")

        date_from = parse_date(date_from_raw) if date_from_raw else None
        date_to = parse_date(date_to_raw) if date_to_raw else None

        if date_from_raw and not date_from:
            return Response(
                {"detail": "Invalid from date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if date_to_raw and not date_to:
            return Response(
                {"detail": "Invalid to date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        progress = get_exercise_progress(
            user=request.user,
            exercise_id=exercise_id_int,
            date_from=date_from,
            date_to=date_to,
        )

        return Response(
            [
                {
                    "date": row["date"],
                    "avg_weight": row["avg_weight"],
                    "max_weight": row["max_weight"],
                    "total_reps": row["total_reps"],
                    "total_volume": row["total_volume"],
                }
                for row in progress
            ]
        )
