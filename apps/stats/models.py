"""
Statistics models for tracking user productivity and progress.

Models are designed for:
1. Caching computed statistics (performance optimization)
2. Tracking streaks and records
3. Daily/weekly aggregations for charts

Most statistics are computed on-the-fly from Task/TaskCompletion/Goal data,
but these models cache results for faster access.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Abstract base model with timestamps."""

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True


# =============================================================================
# 1. Streak Tracking
# =============================================================================


class UserStreak(TimeStampedModel):
    """
    Tracks user's task completion streaks.
    
    A streak is consecutive days with at least one completed task.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="streak",
        verbose_name=_("user"),
    )
    
    # Current streak
    current_streak = models.PositiveIntegerField(
        _("current streak"),
        default=0,
        help_text=_("Current consecutive days with completed tasks"),
    )
    current_streak_start = models.DateField(
        _("current streak start"),
        null=True,
        blank=True,
        help_text=_("When the current streak started"),
    )
    last_activity_date = models.DateField(
        _("last activity date"),
        null=True,
        blank=True,
        help_text=_("Last date with completed task"),
    )
    
    # Best streak (personal record)
    longest_streak = models.PositiveIntegerField(
        _("longest streak"),
        default=0,
        help_text=_("Longest streak ever achieved"),
    )
    longest_streak_start = models.DateField(
        _("longest streak start"),
        null=True,
        blank=True,
    )
    longest_streak_end = models.DateField(
        _("longest streak end"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("user streak")
        verbose_name_plural = _("user streaks")

    def __str__(self) -> str:
        return f"{self.user.email}: {self.current_streak} days (best: {self.longest_streak})"

    def update_streak(self, activity_date=None):
        """
        Update streak based on activity.
        
        Call this when a task is completed.
        """
        if activity_date is None:
            activity_date = timezone.now().date()

        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)

        if self.last_activity_date == activity_date:
            # Already recorded activity today
            return

        if self.last_activity_date == yesterday:
            # Continuing streak
            self.current_streak += 1
        elif self.last_activity_date == today:
            # Same day, no change
            pass
        else:
            # Streak broken, start new one
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
                self.longest_streak_start = self.current_streak_start
                self.longest_streak_end = self.last_activity_date
            
            self.current_streak = 1
            self.current_streak_start = activity_date

        self.last_activity_date = activity_date
        self.save()

    def check_streak_broken(self):
        """Check if streak is broken (no activity yesterday)."""
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)

        if self.last_activity_date and self.last_activity_date < yesterday:
            # Streak is broken
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
                self.longest_streak_start = self.current_streak_start
                self.longest_streak_end = self.last_activity_date
            
            self.current_streak = 0
            self.current_streak_start = None
            self.save()


# =============================================================================
# 2. Daily Productivity (for charts and peak hours)
# =============================================================================


class DailyProductivity(models.Model):
    """
    Daily aggregated statistics for a user.
    
    Pre-computed for fast chart rendering.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_stats",
        verbose_name=_("user"),
    )
    date = models.DateField(_("date"))
    
    # Task counts
    tasks_completed = models.PositiveIntegerField(
        _("tasks completed"),
        default=0,
    )
    tasks_created = models.PositiveIntegerField(
        _("tasks created"),
        default=0,
    )
    
    # Recurring task completions
    habit_completions = models.PositiveIntegerField(
        _("habit completions"),
        default=0,
        help_text=_("Number of recurring task completions"),
    )
    
    # Time tracking (in minutes)
    total_time_spent = models.PositiveIntegerField(
        _("total time spent"),
        default=0,
        help_text=_("Total minutes spent on tasks"),
    )
    
    # Peak hours (JSON: {"hour": count, ...})
    completions_by_hour = models.JSONField(
        _("completions by hour"),
        default=dict,
        help_text=_("Task completions breakdown by hour (0-23)"),
    )
    
    # Goal progress
    milestones_completed = models.PositiveIntegerField(
        _("milestones completed"),
        default=0,
    )

    class Meta:
        verbose_name = _("daily productivity")
        verbose_name_plural = _("daily productivity records")
        unique_together = ["user", "date"]
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.date}: {self.tasks_completed} tasks"


# =============================================================================
# 3. Habit/Recurring Task Performance
# =============================================================================


class HabitPerformance(TimeStampedModel):
    """
    Performance metrics for recurring tasks (habits).
    
    Tracks consistency, streaks, and trends for each recurring task.
    """

    task = models.OneToOneField(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="performance",
        verbose_name=_("task"),
        limit_choices_to={"is_recurring": True},
    )
    
    # Consistency metrics
    consistency_rate = models.FloatField(
        _("consistency rate"),
        default=0.0,
        help_text=_("Percentage of periods where target was met (0-100)"),
    )
    
    # Streak
    current_streak = models.PositiveIntegerField(
        _("current streak"),
        default=0,
        help_text=_("Current consecutive periods with completion"),
    )
    longest_streak = models.PositiveIntegerField(
        _("longest streak"),
        default=0,
        help_text=_("Longest streak ever"),
    )
    
    # Trend (comparing recent vs older performance)
    trend = models.CharField(
        _("trend"),
        max_length=20,
        choices=[
            ("improving", _("Improving")),
            ("stable", _("Stable")),
            ("declining", _("Declining")),
            ("at_risk", _("At Risk")),
        ],
        default="stable",
    )
    
    # Recent activity
    last_completion_date = models.DateField(
        _("last completion"),
        null=True,
        blank=True,
    )
    completions_last_7_days = models.PositiveIntegerField(
        _("completions (7 days)"),
        default=0,
    )
    completions_last_30_days = models.PositiveIntegerField(
        _("completions (30 days)"),
        default=0,
    )
    
    # Total stats
    total_completions = models.PositiveIntegerField(
        _("total completions"),
        default=0,
    )
    
    # Heatmap data (JSON: {"YYYY-MM-DD": count, ...})
    # Stored for last 365 days
    completion_heatmap = models.JSONField(
        _("completion heatmap"),
        default=dict,
        help_text=_("Daily completion counts for heatmap visualization"),
    )

    class Meta:
        verbose_name = _("habit performance")
        verbose_name_plural = _("habit performances")

    def __str__(self) -> str:
        return f"{self.task.title}: {self.consistency_rate:.1f}% consistency"


# =============================================================================
# 4. Goal Progress Statistics
# =============================================================================


class GoalProgress(TimeStampedModel):
    """
    Progress statistics for goals.
    
    Tracks velocity, predictions, and milestone completion.
    """

    goal = models.OneToOneField(
        "goals.Goal",
        on_delete=models.CASCADE,
        related_name="progress_stats",
        verbose_name=_("goal"),
    )
    
    # Progress metrics
    progress_percentage = models.FloatField(
        _("progress percentage"),
        default=0.0,
        help_text=_("Overall completion percentage (0-100)"),
    )
    
    # Velocity (progress per day)
    velocity = models.FloatField(
        _("velocity"),
        default=0.0,
        help_text=_("Progress percentage per day"),
    )
    velocity_trend = models.CharField(
        _("velocity trend"),
        max_length=20,
        choices=[
            ("accelerating", _("Accelerating")),
            ("steady", _("Steady")),
            ("slowing", _("Slowing")),
            ("stalled", _("Stalled")),
        ],
        default="steady",
    )
    
    # Milestones
    milestones_total = models.PositiveIntegerField(
        _("total milestones"),
        default=0,
    )
    milestones_completed = models.PositiveIntegerField(
        _("completed milestones"),
        default=0,
    )
    
    # Tasks linked to goal
    tasks_total = models.PositiveIntegerField(
        _("total tasks"),
        default=0,
    )
    tasks_completed = models.PositiveIntegerField(
        _("completed tasks"),
        default=0,
    )
    
    # Predictions
    estimated_completion_date = models.DateField(
        _("estimated completion"),
        null=True,
        blank=True,
        help_text=_("Predicted completion date based on current velocity"),
    )
    days_ahead_or_behind = models.IntegerField(
        _("days ahead/behind"),
        default=0,
        help_text=_("Positive = ahead of schedule, Negative = behind"),
    )
    on_track = models.BooleanField(
        _("on track"),
        default=True,
        help_text=_("Whether goal is on track to meet deadline"),
    )
    
    # Activity
    last_activity_date = models.DateField(
        _("last activity"),
        null=True,
        blank=True,
    )
    days_since_activity = models.PositiveIntegerField(
        _("days since activity"),
        default=0,
    )

    class Meta:
        verbose_name = _("goal progress")
        verbose_name_plural = _("goal progress records")

    def __str__(self) -> str:
        return f"{self.goal.title}: {self.progress_percentage:.1f}%"


# =============================================================================
# 5. Personal Records
# =============================================================================


class PersonalRecord(TimeStampedModel):
    """
    Personal bests and records for gamification.
    """

    class RecordType(models.TextChoices):
        MAX_TASKS_DAY = "max_tasks_day", _("Most tasks in a day")
        MAX_TASKS_WEEK = "max_tasks_week", _("Most tasks in a week")
        MAX_HABITS_DAY = "max_habits_day", _("Most habits in a day")
        LONGEST_STREAK = "longest_streak", _("Longest streak")
        FASTEST_GOAL = "fastest_goal", _("Fastest goal completion")
        MOST_PRODUCTIVE_HOUR = "most_productive_hour", _("Most productive hour")
        BEST_WEEK = "best_week", _("Best week ever")
        BEST_MONTH = "best_month", _("Best month ever")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_records",
        verbose_name=_("user"),
    )
    
    record_type = models.CharField(
        _("record type"),
        max_length=30,
        choices=RecordType.choices,
    )
    
    # Record value (integer for counts, can represent different things)
    value = models.PositiveIntegerField(
        _("value"),
        help_text=_("Record value (tasks count, days, etc.)"),
    )
    
    # When record was achieved
    achieved_at = models.DateTimeField(
        _("achieved at"),
        default=timezone.now,
    )
    achieved_date = models.DateField(
        _("achieved date"),
        help_text=_("Date when record was set"),
    )
    
    # Additional context (JSON)
    context = models.JSONField(
        _("context"),
        default=dict,
        blank=True,
        help_text=_("Additional context about the record"),
    )
    
    # Is this the current record?
    is_current = models.BooleanField(
        _("is current"),
        default=True,
        help_text=_("Whether this is the current record (not beaten)"),
    )

    class Meta:
        verbose_name = _("personal record")
        verbose_name_plural = _("personal records")
        ordering = ["-achieved_at"]
        indexes = [
            models.Index(fields=["user", "record_type", "is_current"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.get_record_type_display()}: {self.value}"


# =============================================================================
# 6. Weekly/Monthly Comparisons Cache
# =============================================================================


class PeriodComparison(TimeStampedModel):
    """
    Cached comparison data between periods.
    
    Pre-computed for quick "this week vs last week" views.
    """

    class PeriodType(models.TextChoices):
        WEEK = "week", _("Week")
        MONTH = "month", _("Month")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="period_comparisons",
        verbose_name=_("user"),
    )
    
    period_type = models.CharField(
        _("period type"),
        max_length=10,
        choices=PeriodType.choices,
    )
    
    # Period identifiers
    period_start = models.DateField(_("period start"))
    period_end = models.DateField(_("period end"))
    
    # Metrics for this period
    tasks_completed = models.PositiveIntegerField(default=0)
    tasks_created = models.PositiveIntegerField(default=0)
    habit_completions = models.PositiveIntegerField(default=0)
    time_spent_minutes = models.PositiveIntegerField(default=0)
    goals_progressed = models.PositiveIntegerField(default=0)
    milestones_completed = models.PositiveIntegerField(default=0)
    
    # Comparison with previous period
    tasks_change_percent = models.FloatField(
        _("tasks change %"),
        default=0.0,
        help_text=_("Percentage change from previous period"),
    )
    productivity_score = models.PositiveIntegerField(
        _("productivity score"),
        default=0,
        help_text=_("Computed productivity score (0-100)"),
    )

    class Meta:
        verbose_name = _("period comparison")
        verbose_name_plural = _("period comparisons")
        unique_together = ["user", "period_type", "period_start"]
        ordering = ["-period_start"]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.period_type}: {self.period_start}"


# =============================================================================
# 7. Group Rankings (for group feature)
# =============================================================================


class GroupRanking(TimeStampedModel):
    """
    User ranking within a group.
    
    Updated periodically to show leaderboard.
    """

    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        related_name="rankings",
        verbose_name=_("group"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_rankings",
        verbose_name=_("user"),
    )
    
    # Ranking
    rank = models.PositiveIntegerField(
        _("rank"),
        default=0,
        help_text=_("Position in the group (1 = top)"),
    )
    
    # Period (for weekly/monthly rankings)
    period_type = models.CharField(
        _("period type"),
        max_length=10,
        choices=PeriodComparison.PeriodType.choices,
        default=PeriodComparison.PeriodType.WEEK,
    )
    period_start = models.DateField(_("period start"))
    
    # Score components
    tasks_completed = models.PositiveIntegerField(default=0)
    habit_completions = models.PositiveIntegerField(default=0)
    streak_days = models.PositiveIntegerField(default=0)
    goals_progress = models.FloatField(default=0.0)
    
    # Total score
    total_score = models.PositiveIntegerField(
        _("total score"),
        default=0,
        help_text=_("Weighted score for ranking"),
    )
    
    # Change from previous period
    rank_change = models.IntegerField(
        _("rank change"),
        default=0,
        help_text=_("Positive = moved up, Negative = moved down"),
    )

    class Meta:
        verbose_name = _("group ranking")
        verbose_name_plural = _("group rankings")
        unique_together = ["group", "user", "period_type", "period_start"]
        ordering = ["rank"]
        indexes = [
            models.Index(fields=["group", "period_type", "period_start", "rank"]),
        ]

    def __str__(self) -> str:
        return f"{self.group.name} - #{self.rank}: {self.user.email}"

