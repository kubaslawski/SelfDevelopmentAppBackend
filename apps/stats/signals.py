"""
Signals for automatically updating statistics.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.tasks.models import Task, TaskCompletion


@receiver(post_save, sender=TaskCompletion)
def update_stats_on_completion(sender, instance, created, **kwargs):
    """
    Update stats when a task completion is recorded.
    """
    if not created:
        return
    
    task = instance.task
    user = task.user
    
    if not user:
        return
    
    # Update streak
    from .services import update_user_streak
    update_user_streak(user, instance.completed_at.date())
    
    # Update daily productivity
    from .services import update_daily_productivity
    update_daily_productivity(user, instance.completed_at.date())
    
    # Update habit performance
    if task.is_recurring:
        from .services import update_habit_performance
        update_habit_performance(task)
    
    # Check for personal records
    from .services import check_and_update_records
    from .models import PersonalRecord, DailyProductivity
    
    daily = DailyProductivity.objects.filter(
        user=user,
        date=instance.completed_at.date(),
    ).first()
    
    if daily:
        # Check max tasks in a day
        check_and_update_records(
            user,
            PersonalRecord.RecordType.MAX_TASKS_DAY,
            daily.tasks_completed,
            {"date": str(instance.completed_at.date())},
        )
        
        # Check max habits in a day
        check_and_update_records(
            user,
            PersonalRecord.RecordType.MAX_HABITS_DAY,
            daily.habit_completions,
            {"date": str(instance.completed_at.date())},
        )


@receiver(post_save, sender=Task)
def update_stats_on_task_complete(sender, instance, **kwargs):
    """
    Update stats when a non-recurring task is marked complete.
    """
    if not instance.user:
        return
    
    if instance.status == Task.Status.COMPLETED and instance.completed_at:
        # Update streak
        from .services import update_user_streak
        update_user_streak(instance.user, instance.completed_at.date())
        
        # Update daily productivity
        from .services import update_daily_productivity
        update_daily_productivity(instance.user, instance.completed_at.date())

