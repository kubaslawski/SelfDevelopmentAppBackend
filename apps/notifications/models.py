"""
Notification models for task reminders.

Supports:
- Regular tasks: reminders at 6h/3h/1h before due_date
- Recurring daily tasks: reminder 6h before end of day
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


class NotificationPreference(TimeStampedModel):
    """
    User preferences for notifications.

    Controls which reminders the user wants to receive and how.
    """

    class ReminderTime(models.TextChoices):
        """Standard reminder times before deadline."""

        SIX_HOURS = "6h", _("6 hours before")
        THREE_HOURS = "3h", _("3 hours before")
        ONE_HOUR = "1h", _("1 hour before")
        THIRTY_MINUTES = "30m", _("30 minutes before")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name=_("user"),
    )

    # Global settings
    notifications_enabled = models.BooleanField(
        _("notifications enabled"),
        default=True,
        help_text=_("Master switch for all notifications"),
    )
    push_enabled = models.BooleanField(
        _("push notifications enabled"),
        default=True,
        help_text=_("Receive push notifications on mobile"),
    )
    email_enabled = models.BooleanField(
        _("email notifications enabled"),
        default=False,
        help_text=_("Receive notifications via email"),
    )

    # Regular task reminders (before due_date)
    regular_task_reminders = models.JSONField(
        _("regular task reminder times"),
        default=list,
        blank=True,
        help_text=_("List of reminder times for regular tasks, e.g., ['6h', '1h']"),
    )

    # Recurring task reminders
    daily_reminder_enabled = models.BooleanField(
        _("daily recurring reminder"),
        default=True,
        help_text=_("Remind about incomplete daily tasks"),
    )
    daily_reminder_hours_before = models.PositiveIntegerField(
        _("hours before day end"),
        default=6,
        help_text=_("Hours before midnight to send daily task reminder"),
    )

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(
        _("quiet hours enabled"),
        default=True,
        help_text=_("Don't send notifications during quiet hours"),
    )
    quiet_hours_start = models.TimeField(
        _("quiet hours start"),
        default="22:00",
        help_text=_("Start of quiet hours (HH:MM)"),
    )
    quiet_hours_end = models.TimeField(
        _("quiet hours end"),
        default="08:00",
        help_text=_("End of quiet hours (HH:MM)"),
    )

    # Device token for push notifications
    push_token = models.CharField(
        _("push notification token"),
        max_length=512,
        blank=True,
        default="",
        help_text=_("Expo push token for mobile notifications"),
    )

    class Meta:
        verbose_name = _("notification preference")
        verbose_name_plural = _("notification preferences")

    def __str__(self) -> str:
        return f"Notification preferences for {self.user}"

    def save(self, *args, **kwargs):
        # Set default reminder times if empty
        if not self.regular_task_reminders:
            self.regular_task_reminders = ["6h", "1h"]
        super().save(*args, **kwargs)


class Notification(TimeStampedModel):
    """
    Individual notification record.

    Tracks what notifications have been sent/scheduled for each task.
    """

    class NotificationType(models.TextChoices):
        """Type of notification."""

        TASK_REMINDER = "task_reminder", _("Task Reminder")
        DAILY_REMINDER = "daily_reminder", _("Daily Recurring Reminder")
        WEEKLY_REMINDER = "weekly_reminder", _("Weekly Recurring Reminder")
        GOAL_REMINDER = "goal_reminder", _("Goal Milestone Reminder")

    class Status(models.TextChoices):
        """Notification delivery status."""

        PENDING = "pending", _("Pending")
        SCHEDULED = "scheduled", _("Scheduled")
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")
        CANCELLED = "cancelled", _("Cancelled")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("user"),
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("task"),
        null=True,
        blank=True,
    )

    # Notification details
    notification_type = models.CharField(
        _("type"),
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.TASK_REMINDER,
    )
    title = models.CharField(
        _("title"),
        max_length=255,
        help_text=_("Notification title"),
    )
    body = models.TextField(
        _("body"),
        help_text=_("Notification message body"),
    )

    # Scheduling
    scheduled_for = models.DateTimeField(
        _("scheduled for"),
        db_index=True,
        help_text=_("When this notification should be sent"),
    )
    reminder_key = models.CharField(
        _("reminder key"),
        max_length=50,
        blank=True,
        default="",
        help_text=_("Unique key for this reminder type (e.g., '6h', '1h')"),
    )

    # Delivery status
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    sent_at = models.DateTimeField(
        _("sent at"),
        null=True,
        blank=True,
    )
    error_message = models.TextField(
        _("error message"),
        blank=True,
        default="",
    )

    # Delivery method tracking
    sent_via_push = models.BooleanField(
        _("sent via push"),
        default=False,
    )
    sent_via_email = models.BooleanField(
        _("sent via email"),
        default=False,
    )

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        ordering = ["-scheduled_for"]
        indexes = [
            models.Index(fields=["user", "status", "scheduled_for"]),
            models.Index(fields=["task", "reminder_key"]),
        ]
        # Prevent duplicate reminders for same task and reminder type
        unique_together = ["task", "reminder_key", "scheduled_for"]

    def __str__(self) -> str:
        return f"{self.notification_type}: {self.title}"

    def mark_sent(self, via_push: bool = False, via_email: bool = False) -> None:
        """Mark notification as sent."""
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.sent_via_push = via_push
        self.sent_via_email = via_email
        self.save(update_fields=[
            "status", "sent_at", "sent_via_push", "sent_via_email", "updated_at"
        ])

    def mark_failed(self, error: str) -> None:
        """Mark notification as failed."""
        self.status = self.Status.FAILED
        self.error_message = error
        self.save(update_fields=["status", "error_message", "updated_at"])

    def cancel(self) -> None:
        """Cancel a pending notification."""
        if self.status == self.Status.PENDING:
            self.status = self.Status.CANCELLED
            self.save(update_fields=["status", "updated_at"])

