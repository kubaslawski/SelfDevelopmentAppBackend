"""
Serializers for Stats app.
"""

from rest_framework import serializers

from .models import (
    DailyProductivity,
    GoalProgress,
    GroupRanking,
    HabitPerformance,
    PeriodComparison,
    PersonalRecord,
    UserStreak,
)


# =============================================================================
# User Streak
# =============================================================================


class UserStreakSerializer(serializers.ModelSerializer):
    """Serializer for user streak data."""

    is_active_today = serializers.SerializerMethodField()
    days_until_streak_lost = serializers.SerializerMethodField()

    class Meta:
        model = UserStreak
        fields = [
            "current_streak",
            "current_streak_start",
            "last_activity_date",
            "longest_streak",
            "longest_streak_start",
            "longest_streak_end",
            "is_active_today",
            "days_until_streak_lost",
            "updated_at",
        ]
        read_only_fields = fields

    def get_is_active_today(self, obj) -> bool:
        """Check if user has completed a task today."""
        from django.utils import timezone
        today = timezone.now().date()
        return obj.last_activity_date == today

    def get_days_until_streak_lost(self, obj) -> int:
        """Days until streak is lost (0 = today is last chance, -1 = already lost)."""
        from django.utils import timezone
        if not obj.last_activity_date or obj.current_streak == 0:
            return -1
        
        today = timezone.now().date()
        days_since_activity = (today - obj.last_activity_date).days
        
        if days_since_activity == 0:
            return 1  # Safe until tomorrow
        elif days_since_activity == 1:
            return 0  # Today is last chance!
        else:
            return -1  # Already lost


# =============================================================================
# Daily Productivity
# =============================================================================


class DailyProductivitySerializer(serializers.ModelSerializer):
    """Serializer for daily productivity stats."""

    class Meta:
        model = DailyProductivity
        fields = [
            "date",
            "tasks_completed",
            "tasks_created",
            "habit_completions",
            "total_time_spent",
            "completions_by_hour",
            "milestones_completed",
        ]
        read_only_fields = fields


class ProductivitySummarySerializer(serializers.Serializer):
    """Summary of productivity stats for a period."""

    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_tasks_completed = serializers.IntegerField()
    total_habit_completions = serializers.IntegerField()
    total_time_spent = serializers.IntegerField()
    average_tasks_per_day = serializers.FloatField()
    peak_hour = serializers.IntegerField(allow_null=True)
    peak_hour_count = serializers.IntegerField()
    best_day = serializers.DateField(allow_null=True)
    best_day_count = serializers.IntegerField()
    daily_breakdown = DailyProductivitySerializer(many=True)


# =============================================================================
# Habit Performance
# =============================================================================


class HabitPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for habit/recurring task performance."""

    task_id = serializers.IntegerField(source="task.id", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True)
    task_recurrence = serializers.CharField(source="task.recurrence_display", read_only=True)

    class Meta:
        model = HabitPerformance
        fields = [
            "task_id",
            "task_title",
            "task_recurrence",
            "consistency_rate",
            "current_streak",
            "longest_streak",
            "trend",
            "last_completion_date",
            "completions_last_7_days",
            "completions_last_30_days",
            "total_completions",
            "completion_heatmap",
            "updated_at",
        ]
        read_only_fields = fields


class HabitSummarySerializer(serializers.Serializer):
    """Summary of all habits performance."""

    total_habits = serializers.IntegerField()
    average_consistency = serializers.FloatField()
    best_habits = HabitPerformanceSerializer(many=True)
    at_risk_habits = HabitPerformanceSerializer(many=True)
    improving_habits = HabitPerformanceSerializer(many=True)


# =============================================================================
# Goal Progress
# =============================================================================


class GoalProgressSerializer(serializers.ModelSerializer):
    """Serializer for goal progress stats."""

    goal_id = serializers.IntegerField(source="goal.id", read_only=True)
    goal_title = serializers.CharField(source="goal.title", read_only=True)
    goal_category = serializers.CharField(source="goal.category", read_only=True)
    goal_target_date = serializers.DateField(source="goal.target_date", read_only=True)

    class Meta:
        model = GoalProgress
        fields = [
            "goal_id",
            "goal_title",
            "goal_category",
            "goal_target_date",
            "progress_percentage",
            "velocity",
            "velocity_trend",
            "milestones_total",
            "milestones_completed",
            "tasks_total",
            "tasks_completed",
            "estimated_completion_date",
            "days_ahead_or_behind",
            "on_track",
            "last_activity_date",
            "days_since_activity",
            "updated_at",
        ]
        read_only_fields = fields


class GoalsSummarySerializer(serializers.Serializer):
    """Summary of all goals progress."""

    total_goals = serializers.IntegerField()
    active_goals = serializers.IntegerField()
    on_track_count = serializers.IntegerField()
    behind_count = serializers.IntegerField()
    average_progress = serializers.FloatField()
    goals = GoalProgressSerializer(many=True)


# =============================================================================
# Personal Records
# =============================================================================


class PersonalRecordSerializer(serializers.ModelSerializer):
    """Serializer for personal records."""

    record_type_display = serializers.CharField(source="get_record_type_display", read_only=True)

    class Meta:
        model = PersonalRecord
        fields = [
            "id",
            "record_type",
            "record_type_display",
            "value",
            "achieved_at",
            "achieved_date",
            "context",
            "is_current",
        ]
        read_only_fields = fields


class PersonalRecordsSummarySerializer(serializers.Serializer):
    """Summary of all personal records."""

    records = PersonalRecordSerializer(many=True)
    recent_records = PersonalRecordSerializer(many=True)


# =============================================================================
# Period Comparison
# =============================================================================


class PeriodComparisonSerializer(serializers.ModelSerializer):
    """Serializer for period comparison."""

    class Meta:
        model = PeriodComparison
        fields = [
            "period_type",
            "period_start",
            "period_end",
            "tasks_completed",
            "tasks_created",
            "habit_completions",
            "time_spent_minutes",
            "goals_progressed",
            "milestones_completed",
            "tasks_change_percent",
            "productivity_score",
        ]
        read_only_fields = fields


class ComparisonResultSerializer(serializers.Serializer):
    """Comparison between two periods."""

    current_period = PeriodComparisonSerializer()
    previous_period = PeriodComparisonSerializer(allow_null=True)
    
    # Changes
    tasks_change = serializers.IntegerField()
    tasks_change_percent = serializers.FloatField()
    habits_change = serializers.IntegerField()
    habits_change_percent = serializers.FloatField()
    time_change = serializers.IntegerField()
    time_change_percent = serializers.FloatField()
    
    # Insights
    is_improvement = serializers.BooleanField()
    summary = serializers.CharField()


# =============================================================================
# Group Rankings
# =============================================================================


class GroupRankingSerializer(serializers.ModelSerializer):
    """Serializer for group ranking."""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = GroupRanking
        fields = [
            "rank",
            "user_email",
            "user_name",
            "period_type",
            "period_start",
            "tasks_completed",
            "habit_completions",
            "streak_days",
            "goals_progress",
            "total_score",
            "rank_change",
        ]
        read_only_fields = fields

    def get_user_name(self, obj) -> str:
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class GroupLeaderboardSerializer(serializers.Serializer):
    """Leaderboard for a group."""

    group_id = serializers.IntegerField()
    group_name = serializers.CharField()
    period_type = serializers.CharField()
    period_start = serializers.DateField()
    rankings = GroupRankingSerializer(many=True)
    my_rank = GroupRankingSerializer(allow_null=True)


# =============================================================================
# Dashboard Summary (all stats combined)
# =============================================================================


class DashboardStatsSerializer(serializers.Serializer):
    """Combined dashboard stats."""

    streak = UserStreakSerializer()
    today = DailyProductivitySerializer(allow_null=True)
    this_week = ProductivitySummarySerializer()
    personal_records = PersonalRecordSerializer(many=True)
    top_habits = HabitPerformanceSerializer(many=True)
    active_goals = GoalProgressSerializer(many=True)

