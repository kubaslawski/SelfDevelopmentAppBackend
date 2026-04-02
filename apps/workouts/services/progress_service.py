from datetime import date

from django.db.models import Avg, F, Max, Sum
from django.db.models.functions import TruncDate

from apps.workouts.models import ExerciseSet


def get_exercise_progress(user, exercise_id: int, date_from: date | None, date_to: date | None):
    queryset = ExerciseSet.objects.filter(
        session_exercise__session__user=user,
        session_exercise__exercise_id=exercise_id,
    )

    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    return (
        queryset.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(
            avg_weight=Avg("weight"),
            max_weight=Max("weight"),
            total_reps=Sum("reps"),
            total_volume=Sum(F("reps") * F("weight")),
        )
        .order_by("date")
    )
