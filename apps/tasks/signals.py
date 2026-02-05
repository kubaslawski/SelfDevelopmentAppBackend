"""
Signals for the Tasks app.

Handles automatic notification scheduling and cancellation.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from apps.notifications.services import (
    cancel_task_notifications,
    reschedule_task_reminders,
    schedule_daily_recurring_reminder,
    schedule_task_reminders,
)

from .models import Task, TaskCompletion


@receiver(post_save, sender=Task)
def task_saved(sender, instance, created, **kwargs):
    """
    Handle task creation and updates.
    
    - New task with due_date: schedule reminders
    - New recurring daily task: schedule daily reminder
    - Task completed: cancel pending notifications
    - Task updated with due_date change: reschedule reminders
    """
    # Task completed - cancel all pending notifications
    if instance.status == Task.Status.COMPLETED:
        cancel_task_notifications(instance)
        return

    # Task archived - cancel notifications
    if instance.status == Task.Status.ARCHIVED:
        cancel_task_notifications(instance)
        return

    if created:
        # New task - schedule appropriate reminders
        if instance.is_recurring and instance.recurrence_period == Task.RecurrencePeriod.DAILY:
            schedule_daily_recurring_reminder(instance)
        elif instance.due_date:
            schedule_task_reminders(instance)
    else:
        # Task updated - reschedule if it has a due_date
        # reschedule_task_reminders cancels existing and creates new ones
        if instance.due_date and not instance.is_recurring:
            reschedule_task_reminders(instance)


@receiver(pre_delete, sender=Task)
def task_deleted(sender, instance, **kwargs):
    """Cancel all notifications when task is deleted."""
    cancel_task_notifications(instance)


@receiver(post_save, sender=TaskCompletion)
def completion_created(sender, instance, created, **kwargs):
    """
    Handle task completion for recurring tasks.
    
    When a recurring task reaches its target for the period,
    cancel any pending reminders for that task.
    """
    if not created:
        return

    task = instance.task
    
    # Check if the task is now complete for the current period
    if task.is_period_complete:
        cancel_task_notifications(task)

