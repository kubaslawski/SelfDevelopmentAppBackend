"""
Task models for the Self Development App.
"""

from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Visibility(models.TextChoices):
    """Visibility levels for content (Task/Goal)."""
    PRIVATE = "private", _("Private")
    GROUP = "group", _("Group")
    PUBLIC = "public", _("Public")


class TimeStampedModel(models.Model):
    """
    Abstract base model with created and modified timestamps.
    """

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True


class TaskGroup(TimeStampedModel):
    """
    Group/family of related tasks.

    Allows organizing tasks into logical groups (e.g., "German Learning",
    "Fitness", "Work Projects").
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_groups",
        verbose_name=_("user"),
    )
    name = models.CharField(
        _("name"),
        max_length=100,
        help_text=_("Group name"),
    )
    description = models.TextField(
        _("description"),
        blank=True,
        default="",
        help_text=_("Optional description of this task group"),
    )
    color = models.CharField(
        _("color"),
        max_length=7,
        blank=True,
        default="",
        help_text=_("Hex color code for UI (e.g., #FF5733)"),
    )
    icon = models.CharField(
        _("icon"),
        max_length=64,
        blank=True,
        default="",
        help_text=_("Icon name for UI (e.g., material-community icon key)"),
    )
    is_active = models.BooleanField(
        _("is active"),
        default=True,
        help_text=_("Whether this group is active"),
    )

    class Meta:
        verbose_name = _("task group")
        verbose_name_plural = _("task groups")
        ordering = ["name"]
        unique_together = ["user", "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def task_count(self) -> int:
        """Number of tasks in this group."""
        return self.tasks.count()

    @property
    def completed_task_count(self) -> int:
        """Number of completed tasks in this group."""
        return self.tasks.filter(status=Task.Status.COMPLETED).count()


class Task(TimeStampedModel):
    """
    Task model representing a self-development task or goal.

    Supports recurring tasks with configurable frequency:
    - N times per period (day, week, month, quarter, year)
    - Periods always start from calendar boundaries (1st of month, Monday, Jan 1, etc.)
    - Task completions are tracked in TaskCompletion model
    """

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    class Status(models.TextChoices):
        TODO = "todo", _("To Do")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")
        ARCHIVED = "archived", _("Archived")

    class RecurrencePeriod(models.TextChoices):
        DAILY = "daily", _("Daily")
        WEEKLY = "weekly", _("Weekly")
        BIWEEKLY = "biweekly", _("Every 2 Weeks")
        MONTHLY = "monthly", _("Monthly")
        QUARTERLY = "quarterly", _("Quarterly")
        YEARLY = "yearly", _("Yearly")

    class UnitType(models.TextChoices):
        """Unit type for measuring task goals/progress."""

        # Time-based
        MINUTES = "minutes", _("Minutes")
        HOURS = "hours", _("Hours")
        # Count-based
        COUNT = "count", _("Count/Repetitions")
        PAGES = "pages", _("Pages")
        # Distance
        KILOMETERS = "kilometers", _("Kilometers")
        METERS = "meters", _("Meters")
        # Health
        CALORIES = "calories", _("Calories")
        STEPS = "steps", _("Steps")
        # Custom
        CUSTOM = "custom", _("Custom unit")

    # Basic fields
    title = models.CharField(_("title"), max_length=255, help_text=_("Task title"))
    description = models.TextField(
        _("description"), blank=True, default="", help_text=_("Detailed description of the task")
    )

    # Status and priority
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )
    priority = models.CharField(
        _("priority"),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    # Dates
    due_date = models.DateTimeField(
        _("due date"), null=True, blank=True, help_text=_("Deadline for completing the task")
    )
    completed_at = models.DateTimeField(
        _("completed at"),
        null=True,
        blank=True,
    )

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("user"),
        null=True,
        blank=True,
    )
    goal = models.ForeignKey(
        "goals.Goal",
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("goal"),
        null=True,
        blank=True,
        help_text=_("Goal this task belongs to (auto-deleted with goal)"),
    )
    group = models.ForeignKey(
        TaskGroup,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("task group"),
        null=True,
        blank=True,
        help_text=_("Optional group/family this task belongs to (deleted with group)"),
    )

    # Recurrence settings
    is_recurring = models.BooleanField(
        _("is recurring"), default=False, help_text=_("Whether this task repeats on a schedule")
    )
    recurrence_period = models.CharField(
        _("recurrence period"),
        max_length=20,
        choices=RecurrencePeriod.choices,
        null=True,
        blank=True,
        help_text=_(
            "How often the task should be completed (always starts from calendar boundaries)"
        ),
    )
    recurrence_target_count = models.PositiveIntegerField(
        _("target completions per period"),
        null=True,
        blank=True,
        default=1,
        help_text=_(
            "How many times the task should be completed per period (e.g., 3 times per week)"
        ),
    )
    recurrence_end_date = models.DateField(
        _("recurrence end date"),
        null=True,
        blank=True,
        help_text=_("When the recurring schedule ends (optional)"),
    )

    # Additional metadata
    estimated_duration = models.PositiveIntegerField(
        _("estimated duration (minutes)"),
        null=True,
        blank=True,
        help_text=_("Estimated time to complete the task in minutes"),
    )
    tags = models.CharField(
        _("tags"), max_length=500, blank=True, default="", help_text=_("Comma-separated tags")
    )

    # Goal/target with unit
    unit_type = models.CharField(
        _("unit type"),
        max_length=20,
        choices=UnitType.choices,
        null=True,
        blank=True,
        help_text=_("Type of unit for measuring the goal"),
    )
    custom_unit_name = models.CharField(
        _("custom unit name"),
        max_length=50,
        blank=True,
        default="",
        help_text=_("Name for custom unit (used when unit_type is 'custom')"),
    )
    target_value = models.PositiveIntegerField(
        _("target value"),
        null=True,
        blank=True,
        help_text=_("Target value in the specified unit (e.g., 30 minutes, 50 pages)"),
    )

    # Visibility settings
    visibility = models.CharField(
        _("visibility"),
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
        help_text=_("Who can see this task"),
    )
    shared_with_groups = models.ManyToManyField(
        "groups.Group",
        blank=True,
        related_name="shared_tasks",
        verbose_name=_("shared with groups"),
        help_text=_("Groups this task is shared with (when visibility is 'group')"),
    )

    class Meta:
        verbose_name = _("task")
        verbose_name_plural = _("tasks")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["is_recurring"]),
        ]

    def __str__(self):
        return self.title

    def mark_completed(self):
        """
        Mark the task as completed.

        For recurring tasks, this creates a TaskCompletion record
        instead of marking the task itself as completed.
        """
        if self.is_recurring:
            # For recurring tasks, create a completion record
            TaskCompletion.objects.create(task=self)
        else:
            # For non-recurring tasks, mark as completed
            self.status = self.Status.COMPLETED
            self.completed_at = timezone.now()
            self.save(update_fields=["status", "completed_at", "updated_at"])

    def get_completions_in_period(self, start_date=None, end_date=None):
        """
        Get all completions within a date range.

        Args:
            start_date: Start of the period (defaults to current period start)
            end_date: End of the period (defaults to current period end)

        Returns:
            QuerySet of TaskCompletion objects
        """
        if start_date is None:
            start_date = self._get_current_period_start()

        if end_date is None:
            end_date = self._get_current_period_end()

        return self.completions.filter(completed_at__gte=start_date, completed_at__lt=end_date)

    def _get_current_period_start(self):
        """
        Calculate the start of the current recurrence period.

        Always uses calendar boundaries:
        - Daily: 00:00 of current day
        - Weekly: Monday 00:00 of current week
        - Biweekly: Monday 00:00 of current 2-week period (based on ISO week)
        - Monthly: 1st day 00:00 of current month
        - Quarterly: 1st day 00:00 of current quarter (Jan, Apr, Jul, Oct)
        - Yearly: January 1st 00:00 of current year
        """
        now = timezone.now()

        if self.recurrence_period == self.RecurrencePeriod.DAILY:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)

        elif self.recurrence_period == self.RecurrencePeriod.WEEKLY:
            # Monday of current week
            days_since_monday = now.weekday()
            period_start = now - timedelta(days=days_since_monday)
            return period_start.replace(hour=0, minute=0, second=0, microsecond=0)

        elif self.recurrence_period == self.RecurrencePeriod.BIWEEKLY:
            # Use ISO week number to determine which 2-week period we're in
            # Even weeks start a new period
            iso_week = now.isocalendar()[1]
            weeks_offset = iso_week % 2  # 0 if even week, 1 if odd week
            days_since_monday = now.weekday()
            period_start = now - timedelta(days=days_since_monday + (weeks_offset * 7))
            return period_start.replace(hour=0, minute=0, second=0, microsecond=0)

        elif self.recurrence_period == self.RecurrencePeriod.MONTHLY:
            # 1st of current month
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        elif self.recurrence_period == self.RecurrencePeriod.QUARTERLY:
            # 1st of current quarter (Jan=1, Apr=4, Jul=7, Oct=10)
            quarter_month = ((now.month - 1) // 3) * 3 + 1
            return now.replace(
                month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0
            )

        elif self.recurrence_period == self.RecurrencePeriod.YEARLY:
            # January 1st of current year
            return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def _get_current_period_end(self):
        """
        Calculate the end of the current recurrence period.

        Returns the start of the next period (exclusive boundary).
        """
        period_start = self._get_current_period_start()

        if self.recurrence_period == self.RecurrencePeriod.DAILY:
            return period_start + timedelta(days=1)

        elif self.recurrence_period == self.RecurrencePeriod.WEEKLY:
            return period_start + timedelta(weeks=1)

        elif self.recurrence_period == self.RecurrencePeriod.BIWEEKLY:
            return period_start + timedelta(weeks=2)

        elif self.recurrence_period == self.RecurrencePeriod.MONTHLY:
            return period_start + relativedelta(months=1)

        elif self.recurrence_period == self.RecurrencePeriod.QUARTERLY:
            return period_start + relativedelta(months=3)

        elif self.recurrence_period == self.RecurrencePeriod.YEARLY:
            return period_start + relativedelta(years=1)

        return period_start + timedelta(days=1)

    @property
    def current_period_start(self):
        """Get the start of the current period (for API exposure)."""
        if not self.is_recurring:
            return None
        return self._get_current_period_start()

    @property
    def current_period_end(self):
        """Get the end of the current period (for API exposure)."""
        if not self.is_recurring:
            return None
        return self._get_current_period_end()

    @property
    def completions_in_current_period(self):
        """Get the number of completions in the current period."""
        if not self.is_recurring:
            return 0
        return self.get_completions_in_period().count()

    @property
    def completed_value_in_current_period(self):
        """Get the sum of completed_value in the current period."""
        if not self.is_recurring:
            return 0
        from django.db.models import Sum

        result = self.get_completions_in_period().aggregate(total=Sum("completed_value"))
        return result["total"] or 0

    @property
    def is_period_complete(self):
        """Check if the recurring task has been completed enough times/value this period."""
        if not self.is_recurring:
            return self.status == self.Status.COMPLETED

        # If target_value is set, check sum of completed_value vs target_value
        if self.target_value:
            return self.completed_value_in_current_period >= self.target_value

        # Otherwise check count of completions vs recurrence_target_count
        target = self.recurrence_target_count or 1
        return self.completions_in_current_period >= target

    @property
    def remaining_completions_in_period(self):
        """Get the number of remaining completions/value needed in the current period."""
        if not self.is_recurring:
            return 0 if self.status == self.Status.COMPLETED else 1

        # If target_value is set, return remaining value
        if self.target_value:
            completed = self.completed_value_in_current_period
            return max(0, self.target_value - completed)

        # Otherwise return remaining count
        target = self.recurrence_target_count or 1
        completed = self.completions_in_current_period
        return max(0, target - completed)

    @property
    def last_completion(self):
        """Get the most recent completion timestamp."""
        if self.is_recurring:
            last = self.completions.order_by("-completed_at").first()
            return last.completed_at if last else None
        return self.completed_at

    @property
    def is_overdue(self):
        """Check if the task is overdue."""
        if self.due_date and self.status != self.Status.COMPLETED:
            return timezone.now() > self.due_date
        return False

    @property
    def tags_list(self):
        """Return tags as a list."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
        return []

    @property
    def recurrence_display(self):
        """Human-readable recurrence description."""
        if not self.is_recurring:
            return None

        target = self.recurrence_target_count or 1
        period = self.get_recurrence_period_display() if self.recurrence_period else "period"

        if target == 1:
            return f"Once {period.lower()}"
        return f"{target} times {period.lower()}"

    @property
    def unit_display_name(self):
        """Get the display name for the unit (for chart Y-axis, etc.)."""
        if not self.unit_type:
            return None

        if self.unit_type == self.UnitType.CUSTOM:
            return self.custom_unit_name or "units"

        # Map unit types to short display names
        unit_names = {
            self.UnitType.MINUTES: "min",
            self.UnitType.HOURS: "h",
            self.UnitType.COUNT: "x",
            self.UnitType.PAGES: "pages",
            self.UnitType.KILOMETERS: "km",
            self.UnitType.METERS: "m",
            self.UnitType.CALORIES: "kcal",
            self.UnitType.STEPS: "steps",
        }
        return unit_names.get(self.unit_type, self.unit_type)

    @property
    def goal_display(self):
        """Human-readable goal description with unit."""
        if not self.target_value or not self.unit_type:
            return None

        unit = self.unit_display_name

        # Special formatting for time
        if self.unit_type == self.UnitType.MINUTES:
            if self.target_value >= 60:
                hours = self.target_value // 60
                minutes = self.target_value % 60
                if minutes:
                    return f"{hours}h {minutes}min"
                return f"{hours}h"
            return f"{self.target_value} min"

        elif self.unit_type == self.UnitType.HOURS:
            return f"{self.target_value}h"

        return f"{self.target_value} {unit}"

    @property
    def target_in_minutes(self):
        """Get target value converted to minutes (for time units)."""
        if not self.target_value or not self.unit_type:
            return None

        if self.unit_type == self.UnitType.MINUTES:
            return self.target_value
        elif self.unit_type == self.UnitType.HOURS:
            return self.target_value * 60

        return None  # COUNT type doesn't convert to minutes

    def clean(self):
        """Validate the model."""
        super().clean()

        if self.is_recurring:
            if not self.recurrence_period:
                raise ValidationError(
                    {"recurrence_period": _("Recurrence period is required for recurring tasks.")}
                )


class TaskCompletion(models.Model):
    """
    Records individual completions of recurring tasks.

    Each time a recurring task is completed, a new record is created here.
    This allows tracking of completion history and calculating progress
    towards recurring goals.
    """

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="completions",
        verbose_name=_("task"),
    )
    completed_at = models.DateTimeField(
        _("completed at"),
        default=timezone.now,  # Use default instead of auto_now_add to allow custom values
        db_index=True,
    )
    completed_value = models.PositiveIntegerField(
        _("completed value"),
        null=True,
        blank=True,
        help_text=_("Completed amount in the task's unit (minutes, hours, or count)"),
    )
    notes = models.TextField(
        _("notes"), blank=True, default="", help_text=_("Optional notes about this completion")
    )
    duration_minutes = models.PositiveIntegerField(
        _("actual duration (minutes)"),
        null=True,
        blank=True,
        help_text=_("How long it actually took to complete (legacy, use completed_value)"),
    )

    class Meta:
        verbose_name = _("task completion")
        verbose_name_plural = _("task completions")
        ordering = ["-completed_at"]
        indexes = [
            models.Index(fields=["task", "completed_at"]),
            models.Index(fields=["completed_at"]),
        ]

    def __str__(self):
        return f"{self.task.title} - {self.completed_at.strftime('%Y-%m-%d %H:%M')}"
