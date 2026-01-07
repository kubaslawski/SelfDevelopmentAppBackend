"""
Filters for the Tasks app.
"""
import django_filters

from .models import Task, TaskCompletion


class TaskFilter(django_filters.FilterSet):
    """
    Filter for Task model.

    Allows filtering by:
    - status: exact match or list
    - priority: exact match or list
    - is_recurring: boolean
    - recurrence_period: exact match
    - due_date: range (before/after)
    - created_at: range (before/after)
    - tags: contains
    """

    due_date_before = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='lte',
        label='Due before'
    )
    due_date_after = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='gte',
        label='Due after'
    )
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created after'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created before'
    )
    tags_contains = django_filters.CharFilter(
        field_name='tags',
        lookup_expr='icontains',
        label='Tags contain'
    )
    has_due_date = django_filters.BooleanFilter(
        field_name='due_date',
        lookup_expr='isnull',
        exclude=True,
        label='Has due date'
    )
    recurrence_end_before = django_filters.DateFilter(
        field_name='recurrence_end_date',
        lookup_expr='lte',
        label='Recurrence ends before'
    )
    recurrence_end_after = django_filters.DateFilter(
        field_name='recurrence_end_date',
        lookup_expr='gte',
        label='Recurrence ends after'
    )

    class Meta:
        model = Task
        fields = {
            'status': ['exact', 'in'],
            'priority': ['exact', 'in'],
            'is_recurring': ['exact'],
            'recurrence_period': ['exact', 'in'],
        }


class TaskCompletionFilter(django_filters.FilterSet):
    """
    Filter for TaskCompletion model.

    Allows filtering by:
    - task: exact match
    - completed_at: range (before/after)
    """

    completed_after = django_filters.DateTimeFilter(
        field_name='completed_at',
        lookup_expr='gte',
        label='Completed after'
    )
    completed_before = django_filters.DateTimeFilter(
        field_name='completed_at',
        lookup_expr='lte',
        label='Completed before'
    )
    completed_on = django_filters.DateFilter(
        field_name='completed_at',
        lookup_expr='date',
        label='Completed on date'
    )

    class Meta:
        model = TaskCompletion
        fields = {
            'task': ['exact'],
        }
