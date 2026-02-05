"""
Celery configuration for SelfDevelopmentAppBackend.

This module configures Celery for async task processing and scheduled tasks.
"""

import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# Create the Celery app
app = Celery("selfdevelopmentapp")

# Load config from Django settings with CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# =============================================================================
# Celery Beat Schedule (periodic tasks)
# =============================================================================

app.conf.beat_schedule = {
    # Send pending notifications every minute
    "send-pending-notifications": {
        "task": "apps.notifications.tasks.send_pending_notifications",
        "schedule": 60.0,  # Every 60 seconds
    },
    # Schedule daily recurring reminders at 6:00 AM
    "schedule-daily-reminders": {
        "task": "apps.notifications.tasks.schedule_daily_reminders",
        "schedule": crontab(hour=6, minute=0),
    },
    # Clean up old sent notifications (weekly, Sunday 3:00 AM)
    "cleanup-old-notifications": {
        "task": "apps.notifications.tasks.cleanup_old_notifications",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
    },
    # Motivational quotes twice daily
    "schedule-motivational-quotes-morning": {
        "task": "apps.notifications.tasks.schedule_motivational_quotes",
        "schedule": crontab(hour=9, minute=0),
        "args": ("09:00",),
    },
    "schedule-motivational-quotes-evening": {
        "task": "apps.notifications.tasks.schedule_motivational_quotes",
        "schedule": crontab(hour=17, minute=0),
        "args": ("17:00",),
    },
}

app.conf.timezone = "Europe/Warsaw"


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connection."""
    print(f"Request: {self.request!r}")

