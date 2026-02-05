"""
Notification services for scheduling and sending reminders.

Handles:
- Regular tasks: reminders at 6h/3h/1h before due_date
- Recurring daily tasks: reminder 6h before end of day
- Sending push notifications via Expo Push API
"""

import logging
from datetime import datetime, time, timedelta
from typing import Optional

import requests
from core.llm import LLMError, gemini_client
from core.llm.prompts import (
    MOTIVATIONAL_QUOTES_SYSTEM,
    format_motivational_quotes_prompt,
)
from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone
from pydantic import ValidationError

from apps.tasks.models import Task

from .dto import LLMQuotesResponseDTO
from .entities import MotivationalQuote
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
        logger.info(f"Scheduled {reminder_key} reminder for task {task.id} at {scheduled_for}")

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
    logger.info(f"Scheduled daily reminder for task {task.id} at {scheduled_for}")
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
# Notification Type Styling
# =============================================================================

# Emoji prefixes for each notification type
NOTIFICATION_STYLE = {
    # Reminders
    "task_reminder": {"emoji": "⏰", "category": "reminder"},
    "daily_reminder": {"emoji": "📅", "category": "reminder"},
    "weekly_reminder": {"emoji": "📆", "category": "reminder"},
    "goal_reminder": {"emoji": "🎯", "category": "reminder"},
    # Warnings
    "warning": {"emoji": "⚠️", "category": "warning"},
    "deadline_warning": {"emoji": "🚨", "category": "warning"},
    # Suggestions
    "suggestion": {"emoji": "💡", "category": "suggestion"},
    "tip": {"emoji": "✨", "category": "suggestion"},
    # Congratulations
    "congratulations": {"emoji": "🎉", "category": "congratulations"},
    "achievement": {"emoji": "🏆", "category": "congratulations"},
    "streak": {"emoji": "🔥", "category": "congratulations"},
    # Info
    "info": {"emoji": "ℹ️", "category": "info"},
    "motivational_quote": {"emoji": "✨", "category": "suggestion"},
}


def get_notification_emoji(notification_type: str) -> str:
    """Get emoji for notification type."""
    style = NOTIFICATION_STYLE.get(notification_type, {})
    return style.get("emoji", "📬")


def get_notification_category(notification_type: str) -> str:
    """Get category for notification type."""
    style = NOTIFICATION_STYLE.get(notification_type, {})
    return style.get("category", "info")


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


# =============================================================================
# Expo Push Notification Sending
# =============================================================================


def send_push_notification(notification: Notification) -> bool:
    """
    Send a single push notification via Expo Push API.

    Returns True if sent successfully, False otherwise.
    """
    prefs = get_or_create_preferences(notification.user)

    # Check if push is enabled and token exists
    if not prefs.push_enabled or not prefs.push_token:
        logger.info(f"Push disabled or no token for notification {notification.id}")
        notification.mark_failed("Push disabled or no token")
        return False

    # Check quiet hours
    if is_in_quiet_hours(prefs, timezone.now()):
        logger.info(f"In quiet hours, skipping notification {notification.id}")
        return False  # Will be retried later

    # Build payload
    payload = _build_expo_payload(notification, prefs.push_token)

    try:
        response = requests.post(
            settings.EXPO_PUSH_API_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()

        result = response.json()
        return _handle_expo_response(notification, prefs, result)

    except requests.exceptions.Timeout:
        logger.error(f"Timeout sending notification {notification.id}")
        notification.mark_failed("Timeout")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending notification {notification.id}: {e}")
        notification.mark_failed(str(e))
        return False


def send_push_notifications_batch(notifications: list[Notification]) -> dict:
    """
    Send multiple push notifications in a single batch request.

    Expo allows up to 100 notifications per request.
    Returns dict with counts: {"sent": X, "failed": Y, "skipped": Z}
    """
    results = {"sent": 0, "failed": 0, "skipped": 0}

    if not notifications:
        return results

    # Group notifications by user and build payloads
    payloads = []
    notification_map = {}  # Map payload index to notification

    for notification in notifications:
        prefs = get_or_create_preferences(notification.user)

        # Skip if push disabled or no token
        if not prefs.push_enabled or not prefs.push_token:
            notification.mark_failed("Push disabled or no token")
            results["skipped"] += 1
            continue

        # Skip if in quiet hours
        if is_in_quiet_hours(prefs, timezone.now()):
            results["skipped"] += 1
            continue

        payload = _build_expo_payload(notification, prefs.push_token)
        notification_map[len(payloads)] = (notification, prefs)
        payloads.append(payload)

    if not payloads:
        return results

    # Send batch request
    try:
        response = requests.post(
            settings.EXPO_PUSH_API_URL,
            json=payloads,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()
        data = result.get("data", [])

        # Process each response
        for idx, ticket in enumerate(data):
            if idx not in notification_map:
                continue

            notification, prefs = notification_map[idx]

            if ticket.get("status") == "ok":
                notification.mark_sent(via_push=True)
                results["sent"] += 1
                logger.info(f"Sent notification {notification.id}")
            else:
                error = ticket.get("message", "Unknown error")
                details = ticket.get("details", {})

                # Handle specific errors
                if details.get("error") == "DeviceNotRegistered":
                    # Token is invalid, remove it
                    prefs.push_token = ""
                    prefs.save(update_fields=["push_token", "updated_at"])
                    logger.warning(f"Removed invalid token for user {notification.user_id}")

                notification.mark_failed(error)
                results["failed"] += 1
                logger.error(f"Failed notification {notification.id}: {error}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Batch request failed: {e}")
        # Mark all as failed
        for notification, _ in notification_map.values():
            notification.mark_failed(str(e))
            results["failed"] += 1

    return results


def _build_expo_payload(notification: Notification, push_token: str) -> dict:
    """Build Expo Push API payload for a notification."""
    emoji = get_notification_emoji(notification.notification_type)
    category = get_notification_category(notification.notification_type)

    # Add emoji to title if not already present
    title = notification.title
    if not any(
        title.startswith(e)
        for e in ["⏰", "📅", "📆", "🎯", "⚠️", "🚨", "💡", "✨", "🎉", "🏆", "🔥", "ℹ️", "📬", "🧪"]
    ):
        title = f"{emoji} {title}"

    payload = {
        "to": push_token,
        "title": title,
        "body": notification.body,
        "sound": "default",
        "priority": "high",
        # Badge count (number on app icon)
        "badge": 1,
        # Android specific
        "channelId": "default",
        # Subtitle (iOS only) - shows category
        "subtitle": _get_category_label(category),
        # Custom data passed to app
        "data": {
            "notification_id": notification.id,
            "notification_type": notification.notification_type,
            "category": category,
        },
    }

    # Add task data if available
    if notification.task:
        payload["data"]["task_id"] = notification.task_id
        payload["data"]["task_title"] = notification.task.title

    return payload


def _get_category_label(category: str) -> str:
    """Get human-readable label for category."""
    labels = {
        "reminder": "Przypomnienie",
        "warning": "Ostrzeżenie",
        "suggestion": "Sugestia",
        "congratulations": "Gratulacje",
        "info": "Informacja",
    }
    return labels.get(category, "")


# =============================================================================
# Quick notification creators
# =============================================================================


def create_notification(
    user,
    notification_type: str,
    title: str,
    body: str,
    task=None,
    scheduled_for=None,
) -> Notification:
    """
    Create a notification of any type.

    Args:
        user: User to notify
        notification_type: One of Notification.NotificationType choices
        title: Notification title (emoji will be added automatically)
        body: Notification body text
        task: Optional related task
        scheduled_for: When to send (default: now)

    Returns:
        Created Notification object
    """
    if scheduled_for is None:
        scheduled_for = timezone.now()

    return Notification.objects.create(
        user=user,
        task=task,
        notification_type=notification_type,
        title=title,
        body=body,
        scheduled_for=scheduled_for,
        reminder_key=f"{notification_type}_{timezone.now().timestamp()}",
        status=Notification.Status.PENDING,
    )


def notify_warning(user, title: str, body: str, task=None) -> Notification:
    """Create a warning notification."""
    return create_notification(
        user=user,
        notification_type=Notification.NotificationType.WARNING,
        title=title,
        body=body,
        task=task,
    )


def notify_congratulations(user, title: str, body: str, task=None) -> Notification:
    """Create a congratulations notification."""
    return create_notification(
        user=user,
        notification_type=Notification.NotificationType.CONGRATULATIONS,
        title=title,
        body=body,
        task=task,
    )


def notify_achievement(user, title: str, body: str, task=None) -> Notification:
    """Create an achievement notification."""
    return create_notification(
        user=user,
        notification_type=Notification.NotificationType.ACHIEVEMENT,
        title=title,
        body=body,
        task=task,
    )


def notify_streak(user, title: str, body: str, task=None) -> Notification:
    """Create a streak notification."""
    return create_notification(
        user=user,
        notification_type=Notification.NotificationType.STREAK,
        title=title,
        body=body,
        task=task,
    )


def notify_suggestion(user, title: str, body: str, task=None) -> Notification:
    """Create a suggestion notification."""
    return create_notification(
        user=user,
        notification_type=Notification.NotificationType.SUGGESTION,
        title=title,
        body=body,
        task=task,
    )


def notify_tip(user, title: str, body: str) -> Notification:
    """Create a tip notification."""
    return create_notification(
        user=user,
        notification_type=Notification.NotificationType.TIP,
        title=title,
        body=body,
    )


def notify_info(user, title: str, body: str) -> Notification:
    """Create an info notification."""
    return create_notification(
        user=user,
        notification_type=Notification.NotificationType.INFO,
        title=title,
        body=body,
    )


# =============================================================================
# Motivational Quotes (LLM)
# =============================================================================


def generate_motivational_quotes(user, quote_count: int = 3) -> list[MotivationalQuote]:
    """
    Generate motivational quotes based on user's current goals and tasks.

    Args:
        user: User to personalize quotes for.
        quote_count: Number of quotes to generate (1-5).

    Returns:
        List of MotivationalQuote entities.
    """
    quote_count = max(1, min(quote_count, 5))

    tasks = list(
        Task.objects.filter(user=user)
        .exclude(
            status__in=[
                Task.Status.COMPLETED,
                Task.Status.ARCHIVED,
            ]
        )
        .order_by("due_date")[:10]
    )

    tasks = [task for task in tasks if _has_useful_task_context(task)]
    if not tasks:
        return []

    tasks_text = _format_tasks_context(tasks)
    prompt = format_motivational_quotes_prompt(
        tasks_text=tasks_text,
        quote_count=quote_count,
    )

    try:
        response = gemini_client.generate_json(
            prompt=prompt,
            user_id=user.id,
            system_prompt=MOTIVATIONAL_QUOTES_SYSTEM,
        )
        parsed = LLMQuotesResponseDTO(**response)
    except ValidationError as exc:
        logger.error("Invalid LLM response for motivational quotes: %s", exc)
        raise LLMError("Invalid LLM response format for motivational quotes.")

    quotes = [
        MotivationalQuote(
            text=item.text,
            focus_goal=item.focus_goal,
            focus_task=item.focus_task,
        )
        for item in parsed.quotes
    ]

    if not quotes:
        return []

    _record_motivational_quote_notification(user, quotes)

    return quotes


def _handle_expo_response(
    notification: Notification, prefs: NotificationPreference, result: dict
) -> bool:
    """Handle Expo Push API response for a single notification."""
    data = result.get("data", [])

    if not data:
        notification.mark_failed("Empty response from Expo")
        return False

    # Handle both single object and list responses
    ticket = data[0] if isinstance(data, list) else data

    if ticket.get("status") == "ok":
        notification.mark_sent(via_push=True)
        logger.info(f"Sent notification {notification.id}")
        return True
    else:
        error = ticket.get("message", "Unknown error")
        details = ticket.get("details", {})

        # Handle DeviceNotRegistered - remove invalid token
        if details.get("error") == "DeviceNotRegistered":
            prefs.push_token = ""
            prefs.save(update_fields=["push_token", "updated_at"])
            logger.warning(f"Removed invalid token for user {notification.user_id}")

        notification.mark_failed(error)
        logger.error(f"Failed notification {notification.id}: {error}")
        return False


def _record_motivational_quote_notification(
    user,
    quotes: list[MotivationalQuote],
) -> None:
    """Save a notification record for motivational quote generation."""
    now = timezone.now()
    count = len(quotes)
    title = "Motywujące cytaty"
    if count == 1:
        body = "Wygenerowano 1 cytat motywacyjny."
    else:
        body = f"Wygenerowano {count} cytaty motywacyjne."

    if count > 0:
        body = f"{body} Przykład: {quotes[0].text}"

    Notification.objects.create(
        user=user,
        notification_type=Notification.NotificationType.MOTIVATIONAL_QUOTE,
        title=title,
        body=body,
        scheduled_for=now,
        reminder_key=f"motivational_quote_{now.timestamp()}",
        status=Notification.Status.SENT,
        sent_at=now,
    )


def _format_tasks_context(tasks: list[Task]) -> str:
    """Format tasks for LLM prompt context."""
    if not tasks:
        return "Brak aktywnych zadań."

    return "\n".join(_format_task_context(task) for task in tasks)


def _format_task_context(task: Task) -> str:
    """Format a single task line."""
    due_date = task.due_date.isoformat() if task.due_date else "brak terminu"
    description = task.description.strip() if task.description else ""
    details = (
        f"- {task.title} | opis: {description} | "
        f"status: {task.status} | priorytet: {task.priority} | termin: {due_date}"
    )
    return details


def _has_useful_task_context(task: Task) -> bool:
    """Check if task has enough detail to generate a meaningful quote."""
    title = task.title.strip()
    description = task.description.strip() if task.description else ""
    title_lower = title.lower()
    description_lower = description.lower()

    if len(title) < 4 and len(description) < 15:
        return False

    generic_titles = {
        "zadanie",
        "task",
        "todo",
        "do zrobienia",
        "sprawa",
        "test",
        "abc",
    }
    if title_lower in generic_titles and len(description) < 15:
        return False

    if len(description) >= 15:
        return True

    if len(title) >= 8 and not any(token in title_lower for token in generic_titles):
        return True

    if any(
        token in description_lower
        for token in ["czyt", "książ", "inwest", "kurs", "trening", "nauka"]
    ):
        return True

    return False
