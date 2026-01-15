"""Admin configuration for Stats app."""

from django.contrib import admin

from .models import (
    DailyProductivity,
    GoalProgress,
    GroupRanking,
    HabitPerformance,
    PeriodComparison,
    PersonalRecord,
    UserStreak,
)


@admin.register(UserStreak)
class UserStreakAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "current_streak",
        "longest_streak",
        "last_activity_date",
        "updated_at",
    ]
    list_filter = ["updated_at"]
    search_fields = ["user__email"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(DailyProductivity)
class DailyProductivityAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "date",
        "tasks_completed",
        "habit_completions",
        "total_time_spent",
    ]
    list_filter = ["date"]
    search_fields = ["user__email"]
    date_hierarchy = "date"


@admin.register(HabitPerformance)
class HabitPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        "task",
        "consistency_rate",
        "current_streak",
        "trend",
        "last_completion_date",
    ]
    list_filter = ["trend", "updated_at"]
    search_fields = ["task__title", "task__user__email"]


@admin.register(GoalProgress)
class GoalProgressAdmin(admin.ModelAdmin):
    list_display = [
        "goal",
        "progress_percentage",
        "velocity",
        "on_track",
        "estimated_completion_date",
    ]
    list_filter = ["on_track", "velocity_trend"]
    search_fields = ["goal__title", "goal__user__email"]


@admin.register(PersonalRecord)
class PersonalRecordAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "record_type",
        "value",
        "achieved_date",
        "is_current",
    ]
    list_filter = ["record_type", "is_current", "achieved_date"]
    search_fields = ["user__email"]


@admin.register(PeriodComparison)
class PeriodComparisonAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "period_type",
        "period_start",
        "tasks_completed",
        "productivity_score",
    ]
    list_filter = ["period_type", "period_start"]
    search_fields = ["user__email"]


@admin.register(GroupRanking)
class GroupRankingAdmin(admin.ModelAdmin):
    list_display = [
        "group",
        "user",
        "rank",
        "total_score",
        "period_type",
        "period_start",
    ]
    list_filter = ["group", "period_type", "period_start"]
    search_fields = ["user__email", "group__name"]

