"""
Notification services for scheduling and sending reminders.

Handles:
- Regular tasks: reminders at 6h/3h/1h before due_date
- Recurring daily tasks: reminder 6h before end of day
"""

import logging
from datetime import datetime, time, timedelta
from typing import Optional

from django.db.models import QuerySet
from django.utils import timezone

from apps.tasks.models import Task

from .models import Notification, NotificationPreference

logger = logging.getLogger(__name__)


# Reminder time mappings
REMINDER_TIMEDELTAS = {
    "6h": timedelta(hours=6),
    "3h": timedelta(hours=3),
    "1h": timedelta(hours=1),
    "30m": timedelta(minutes=30),
}


def get_or_create_preferences(user) -> NotificationPreference:
    """Get or create notification preferences for a user."""
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    return prefs


def is_in_quiet_hours(prefs: NotificationPreference, check_time: datetime) -> bool:
    """Check if a given time falls within quiet hours."""
    if not prefs.quiet_hours_enabled:
        return False

    current_time = check_time.time()
    start = prefs.quiet_hours_start
    end = prefs.quiet_hours_end

    # Handle overnight quiet hours (e.g., 22:00 - 08:00)
    if start > end:
        return current_time >= start or current_time <= end
    else:
        return start <= current_time <= end


def schedule_task_reminders(task: Task) -> list[Notification]:
    """
    Schedule reminders for a regular (non-recurring) task with due_date.

    Creates notifications at configured intervals before due_date.
    Returns list of created notifications.
    """
    if not task.user or not task.due_date:
        return []

    if task.status in [Task.Status.COMPLETED, Task.Status.ARCHIVED]:
        return []

    prefs = get_or_create_preferences(task.user)

    if not prefs.notifications_enabled:
        return []

    created_notifications = []
    reminder_times = prefs.regular_task_reminders or ["6h", "1h"]

    for reminder_key in reminder_times:
        delta = REMINDER_TIMEDELTAS.get(reminder_key)
        if not delta:
            continue

        scheduled_for = task.due_date - delta

        # Skip if scheduled time is in the past
        if scheduled_for <= timezone.now():
            continue

        # Skip if in quiet hours (will be rescheduled)
        if is_in_quiet_hours(prefs, scheduled_for):
            # Schedule for end of quiet hours instead
            quiet_end = datetime.combine(
                scheduled_for.date(),
                prefs.quiet_hours_end,
                tzinfo=scheduled_for.tzinfo,
            )
            if quiet_end <= scheduled_for:
                quiet_end += timedelta(days=1)
            scheduled_for = quiet_end

        # Check if this notification already exists
        existing = Notification.objects.filter(
            task=task,
            reminder_key=reminder_key,
            status__in=[Notification.Status.PENDING, Notification.Status.SCHEDULED],
        ).exists()

        if existing:
            continue

        notification = Notification.objects.create(
            user=task.user,
            task=task,
            notification_type=Notification.NotificationType.TASK_REMINDER,
            title=_build_reminder_title(task, reminder_key),
            body=_build_reminder_body(task, reminder_key),
            scheduled_for=scheduled_for,
            reminder_key=reminder_key,
            status=Notification.Status.PENDING,
        )
        created_notifications.append(notification)
        logger.info(
            f"Scheduled {reminder_key} reminder for task {task.id} at {scheduled_for}"
        )

    return created_notifications


def schedule_daily_recurring_reminder(task: Task) -> Optional[Notification]:
    """
    Schedule end-of-day reminder for incomplete daily recurring task.

    Sends reminder X hours before midnight if task is not complete for today.
    """
    if not task.user or not task.is_recurring:
        return None

    if task.recurrence_period != Task.RecurrencePeriod.DAILY:
        return None

    # Check if task is already complete for today
    if task.is_period_complete:
        return None

    prefs = get_or_create_preferences(task.user)

    if not prefs.notifications_enabled or not prefs.daily_reminder_enabled:
        return None

    # Calculate reminder time (X hours before midnight)
    now = timezone.now()
    today_end = datetime.combine(
        now.date() + timedelta(days=1),
        time(0, 0),
        tzinfo=now.tzinfo,
    )
    hours_before = prefs.daily_reminder_hours_before or 6
    scheduled_for = today_end - timedelta(hours=hours_before)

    # Skip if already past
    if scheduled_for <= now:
        return None

    # Check for existing notification
    reminder_key = f"daily_{now.date().isoformat()}"
    existing = Notification.objects.filter(
        task=task,
        reminder_key=reminder_key,
        status__in=[Notification.Status.PENDING, Notification.Status.SCHEDULED],
    ).exists()

    if existing:
        return None

    notification = Notification.objects.create(
        user=task.user,
        task=task,
        notification_type=Notification.NotificationType.DAILY_REMINDER,
        title=f"📅 Dzienny task: {task.title}",
        body=_build_daily_reminder_body(task),
        scheduled_for=scheduled_for,
        reminder_key=reminder_key,
        status=Notification.Status.PENDING,
    )
    logger.info(
        f"Scheduled daily reminder for task {task.id} at {scheduled_for}"
    )
    return notification


def get_pending_notifications() -> QuerySet[Notification]:
    """Get notifications that are due to be sent."""
    return Notification.objects.filter(
        status=Notification.Status.PENDING,
        scheduled_for__lte=timezone.now(),
    ).select_related("user", "task")


def cancel_task_notifications(task: Task) -> int:
    """Cancel all pending notifications for a task."""
    return Notification.objects.filter(
        task=task,
        status=Notification.Status.PENDING,
    ).update(status=Notification.Status.CANCELLED)


def reschedule_task_reminders(task: Task) -> list[Notification]:
    """
    Reschedule reminders when task due_date changes.

    Cancels existing pending reminders and creates new ones.
    """
    cancel_task_notifications(task)
    return schedule_task_reminders(task)


# =============================================================================
# Helper functions for building notification content
# =============================================================================


def _build_reminder_title(task: Task, reminder_key: str) -> str:
    """Build notification title based on reminder type."""
    time_labels = {
        "6h": "za 6 godzin",
        "3h": "za 3 godziny",
        "1h": "za godzinę",
        "30m": "za 30 minut",
    }
    time_label = time_labels.get(reminder_key, "wkrótce")
    return f"⏰ Termin {time_label}: {task.title}"


def _build_reminder_body(task: Task, reminder_key: str) -> str:
    """Build notification body for task reminder."""
    if task.description:
        return f"{task.description[:100]}..." if len(task.description) > 100 else task.description
    return f"Nie zapomnij o zadaniu: {task.title}"


def _build_daily_reminder_body(task: Task) -> str:
    """Build notification body for daily recurring reminder."""
    remaining = task.remaining_completions_in_period
    if remaining == 1:
        return "Pozostało 1 wykonanie na dzisiaj. Nie zapomnij!"
    elif remaining > 1:
        return f"Pozostało {remaining} wykonań na dzisiaj. Nie zapomnij!"
    return "Wykonaj zadanie przed końcem dnia."

