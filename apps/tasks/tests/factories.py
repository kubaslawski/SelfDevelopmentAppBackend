"""
Factory classes for creating test data.
"""
from datetime import timedelta

import factory
from django.utils import timezone

from apps.tasks.models import Task, TaskCompletion


class TaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating Task instances."""

    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f'Task {n}')
    description = factory.Faker('paragraph')
    status = Task.Status.TODO
    priority = Task.Priority.MEDIUM
    is_recurring = False

    @factory.lazy_attribute
    def due_date(self):
        """Set due date to 7 days from now."""
        return timezone.now() + timedelta(days=7)


class CompletedTaskFactory(TaskFactory):
    """Factory for creating completed Task instances."""

    status = Task.Status.COMPLETED

    @factory.lazy_attribute
    def completed_at(self):
        """Set completed_at to now."""
        return timezone.now()


class OverdueTaskFactory(TaskFactory):
    """Factory for creating overdue Task instances."""

    @factory.lazy_attribute
    def due_date(self):
        """Set due date to 1 day ago."""
        return timezone.now() - timedelta(days=1)


class RecurringTaskFactory(TaskFactory):
    """Factory for creating recurring Task instances."""

    is_recurring = True
    recurrence_period = Task.RecurrencePeriod.WEEKLY
    recurrence_target_count = 3


class TaskCompletionFactory(factory.django.DjangoModelFactory):
    """Factory for creating TaskCompletion instances."""

    class Meta:
        model = TaskCompletion

    task = factory.SubFactory(RecurringTaskFactory)
    notes = factory.Faker('sentence')
    duration_minutes = factory.Faker('random_int', min=5, max=120)
