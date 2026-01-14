"""
Celery tasks for notification processing.

These tasks are scheduled by Celery Beat:
- send_pending_notifications: Every minute
- schedule_daily_reminders: Daily at 6:00 AM
- cleanup_old_notifications: Weekly on Sunday at 3:00 AM
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.tasks.models import Task

from .models import Notification
from .services import (
    get_pending_notifications,
    schedule_daily_recurring_reminder,
    send_push_notifications_batch,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_pending_notifications(self):
    """
    Send all pending notifications that are due.

    Runs every minute via Celery Beat.
    Processes notifications in batches for efficiency.
    """
    try:
        pending = list(
            get_pending_notifications()[: settings.EXPO_PUSH_BATCH_SIZE]
        )

        if not pending:
            logger.debug("No pending notifications to send")
            return {"sent": 0, "failed": 0, "skipped": 0}

        logger.info(f"Processing {len(pending)} pending notifications")
        results = send_push_notifications_batch(pending)

        logger.info(
            f"Notification results: sent={results['sent']}, "
            f"failed={results['failed']}, skipped={results['skipped']}"
        )
        return results

    except Exception as exc:
        logger.error(f"Error in send_pending_notifications: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def schedule_daily_reminders(self):
    """
    Schedule reminders for all incomplete daily recurring tasks.

    Runs daily at 6:00 AM via Celery Beat.
    Creates reminder notifications for tasks that haven't been
    completed today.
    """
    try:
        # Get all active daily recurring tasks
        daily_tasks = Task.objects.filter(
            is_recurring=True,
            recurrence_period=Task.RecurrencePeriod.DAILY,
            status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS],
        ).select_related("user")

        scheduled_count = 0
        skipped_count = 0

        for task in daily_tasks:
            # Check if task is already complete for today
            if task.is_period_complete:
                skipped_count += 1
                continue

            notification = schedule_daily_recurring_reminder(task)
            if notification:
                scheduled_count += 1

        logger.info(
            f"Daily reminders: scheduled={scheduled_count}, "
            f"skipped={skipped_count}"
        )
        return {"scheduled": scheduled_count, "skipped": skipped_count}

    except Exception as exc:
        logger.error(f"Error in schedule_daily_reminders: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def cleanup_old_notifications(self):
    """
    Clean up old sent/cancelled/failed notifications.

    Runs weekly via Celery Beat.
    Removes notifications older than 30 days to keep the database clean.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)

        # Delete old sent notifications
        sent_deleted, _ = Notification.objects.filter(
            status=Notification.Status.SENT,
            sent_at__lt=cutoff_date,
        ).delete()

        # Delete old cancelled notifications
        cancelled_deleted, _ = Notification.objects.filter(
            status=Notification.Status.CANCELLED,
            updated_at__lt=cutoff_date,
        ).delete()

        # Delete old failed notifications
        failed_deleted, _ = Notification.objects.filter(
            status=Notification.Status.FAILED,
            updated_at__lt=cutoff_date,
        ).delete()

        total_deleted = sent_deleted + cancelled_deleted + failed_deleted
        logger.info(
            f"Cleanup: deleted {total_deleted} old notifications "
            f"(sent={sent_deleted}, cancelled={cancelled_deleted}, "
            f"failed={failed_deleted})"
        )

        return {
            "sent_deleted": sent_deleted,
            "cancelled_deleted": cancelled_deleted,
            "failed_deleted": failed_deleted,
            "total_deleted": total_deleted,
        }

    except Exception as exc:
        logger.error(f"Error in cleanup_old_notifications: {exc}")
        raise


@shared_task(bind=True)
def send_single_notification(self, notification_id: int):
    """
    Send a single notification by ID.

    Can be called directly for immediate notification sending.
    """
    try:
        notification = Notification.objects.select_related("user", "task").get(
            id=notification_id
        )

        if notification.status != Notification.Status.PENDING:
            logger.warning(
                f"Notification {notification_id} is not pending "
                f"(status={notification.status})"
            )
            return {"success": False, "reason": "not_pending"}

        results = send_push_notifications_batch([notification])
        return {
            "success": results["sent"] > 0,
            "results": results,
        }

    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return {"success": False, "reason": "not_found"}
    except Exception as exc:
        logger.error(f"Error sending notification {notification_id}: {exc}")
        raise

