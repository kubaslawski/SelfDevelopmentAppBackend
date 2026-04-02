from django.contrib import admin

from .models import (
    Exercise,
    ExerciseSet,
    SessionExercise,
    WorkoutPlan,
    WorkoutPlanExercise,
    WorkoutSession,
)


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "started_at", "ended_at", "created_at")
    search_fields = ("name", "user__email")
    list_filter = ("started_at", "ended_at", "created_at")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(WorkoutPlanExercise)
class WorkoutPlanExerciseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "workout_plan",
        "exercise",
        "order",
        "target_sets",
        "target_reps",
        "rest_time_seconds",
    )
    list_filter = ("workout_plan",)
    search_fields = ("workout_plan__name", "exercise__name")


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "workout_plan", "started_at", "ended_at")
    list_filter = ("started_at", "ended_at")
    search_fields = ("user__email", "workout_plan__name")


@admin.register(SessionExercise)
class SessionExerciseAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "exercise", "order", "started_at", "ended_at")
    list_filter = ("started_at", "ended_at")
    search_fields = ("session__id", "exercise__name")


@admin.register(ExerciseSet)
class ExerciseSetAdmin(admin.ModelAdmin):
    list_display = ("id", "session_exercise", "set_number", "reps", "weight", "created_at")
    list_filter = ("created_at",)
    search_fields = ("session_exercise__exercise__name",)
