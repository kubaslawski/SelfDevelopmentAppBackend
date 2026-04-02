from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class WorkoutPlan(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workout_plans",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "started_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.name


class Exercise(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class WorkoutPlanExercise(models.Model):
    workout_plan = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        related_name="plan_exercises",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="plan_links",
    )
    order = models.PositiveIntegerField()
    target_sets = models.PositiveIntegerField()
    target_reps = models.PositiveIntegerField()
    rest_time_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["workout_plan", "order"],
                name="uniq_workout_plan_order",
            )
        ]
        indexes = [
            models.Index(fields=["workout_plan", "order"]),
            models.Index(fields=["exercise"]),
        ]

    def __str__(self) -> str:
        return f"{self.workout_plan_id}:{self.order}:{self.exercise_id}"


class WorkoutSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workout_sessions",
    )
    workout_plan = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user", "started_at"]),
            models.Index(fields=["workout_plan", "started_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.workout_plan_id}:{self.started_at.isoformat()}"


class SessionExercise(models.Model):
    session = models.ForeignKey(
        WorkoutSession,
        on_delete=models.CASCADE,
        related_name="session_exercises",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="session_exercises",
    )
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        indexes = [
            models.Index(fields=["session", "order"]),
            models.Index(fields=["exercise", "started_at"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["session", "order"], name="uniq_session_order")
        ]

    def __str__(self) -> str:
        return f"{self.session_id}:{self.order}:{self.exercise_id}"


class ExerciseSet(models.Model):
    session_exercise = models.ForeignKey(
        SessionExercise,
        on_delete=models.CASCADE,
        related_name="exercise_sets",
    )
    set_number = models.PositiveIntegerField()
    reps = models.PositiveIntegerField()
    weight = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["set_number"]
        indexes = [
            models.Index(fields=["session_exercise", "set_number"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["session_exercise", "set_number"],
                name="uniq_session_exercise_set_number",
            )
        ]

    def __str__(self) -> str:
        return f"{self.session_exercise_id}:{self.set_number}"
