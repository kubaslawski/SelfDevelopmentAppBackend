"""
Views for the Tasks app.
"""
from django.db.models import Case, When, Value, IntegerField
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import TaskFilter, TaskCompletionFilter
from .models import Task, TaskCompletion
from .serializers import (
    SyncCompletionsResponseSerializer,
    SyncCompletionsSerializer,
    TaskCompletionCreateSerializer,
    TaskCompletionSerializer,
    TaskListSerializer,
    TaskSerializer,
    TaskStatusUpdateSerializer,
    TaskWithCompletionsSerializer,
)

# Priority ordering: low=1, medium=2, high=3, urgent=4
PRIORITY_ORDER = Case(
    When(priority='low', then=Value(1)),
    When(priority='medium', then=Value(2)),
    When(priority='high', then=Value(3)),
    When(priority='urgent', then=Value(4)),
    default=Value(0),
    output_field=IntegerField(),
)


class TaskOrderingFilter(filters.OrderingFilter):
    """
    Custom ordering filter that handles priority field specially.
    Maps 'priority' to numeric ordering instead of alphabetical.
    """

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            # Annotate with priority_order for proper sorting
            queryset = queryset.annotate(priority_order=PRIORITY_ORDER)

            # Replace priority with priority_order in ordering
            new_ordering = []
            for field in ordering:
                if field == 'priority':
                    new_ordering.append('priority_order')
                elif field == '-priority':
                    new_ordering.append('-priority_order')
                else:
                    new_ordering.append(field)

            return queryset.order_by(*new_ordering)

        return queryset


@extend_schema_view(
    list=extend_schema(tags=["Tasks"]),
    create=extend_schema(tags=["Tasks"]),
    retrieve=extend_schema(tags=["Tasks"]),
    update=extend_schema(tags=["Tasks"]),
    partial_update=extend_schema(tags=["Tasks"]),
    destroy=extend_schema(tags=["Tasks"]),
    update_status=extend_schema(tags=["Tasks"]),
    complete=extend_schema(tags=["Tasks"]),
    record_completion=extend_schema(tags=["Tasks"]),
    completions=extend_schema(tags=["Tasks"]),
    stats=extend_schema(tags=["Tasks"]),
    bulk_update_status=extend_schema(tags=["Tasks"]),
    recurring=extend_schema(tags=["Tasks"]),
    sync_completions=extend_schema(tags=["Tasks"]),
)
class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks.

    Provides CRUD operations for tasks with filtering, searching, and ordering.
    Supports recurring tasks with completion tracking.

    list:
        Return a list of all tasks.

    create:
        Create a new task.

    retrieve:
        Return a specific task by ID.

    update:
        Update a task.

    partial_update:
        Partially update a task.

    destroy:
        Delete a task.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, TaskOrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'list':
            return TaskListSerializer
        if self.action == 'update_status':
            return TaskStatusUpdateSerializer
        if self.action == 'retrieve':
            # Include completions in detail view
            return TaskWithCompletionsSerializer
        if self.action == 'record_completion':
            return TaskCompletionCreateSerializer
        return TaskSerializer

    def get_queryset(self):
        """
        Filter tasks by authenticated user.
        """
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        else:
            # Return empty queryset for unauthenticated users
            queryset = queryset.none()
        return queryset

    def perform_create(self, serializer):
        """Associate task with current user if authenticated."""
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update only the status of a task.

        This is a convenience endpoint for quick status updates.
        """
        task = self.get_object()
        serializer = TaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(task, serializer.validated_data)
        return Response(TaskSerializer(task).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark a task as completed.

        For recurring tasks, this creates a completion record.
        For non-recurring tasks, this marks the task as completed.
        """
        task = self.get_object()
        task.mark_completed()
        return Response(TaskWithCompletionsSerializer(task).data)

    @action(detail=True, methods=['post'])
    def record_completion(self, request, pk=None):
        """
        Record a completion for a recurring task.

        This allows recording completions with optional notes and duration.

        Expected payload:
        {
            "notes": "Optional notes about this completion",
            "duration_minutes": 30
        }
        """
        task = self.get_object()

        if not task.is_recurring:
            return Response(
                {'error': 'This action is only available for recurring tasks'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TaskCompletionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        completion = TaskCompletion.objects.create(
            task=task,
            **serializer.validated_data
        )

        return Response({
            'completion': TaskCompletionSerializer(completion).data,
            'task': TaskWithCompletionsSerializer(task).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def completions(self, request, pk=None):
        """
        Get all completions for a recurring task.

        Supports pagination and filtering by date range.
        """
        task = self.get_object()

        if not task.is_recurring:
            return Response(
                {'error': 'This task is not a recurring task'},
                status=status.HTTP_400_BAD_REQUEST
            )

        completions = task.completions.all()

        # Optional date filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            completions = completions.filter(completed_at__gte=start_date)
        if end_date:
            completions = completions.filter(completed_at__lte=end_date)

        page = self.paginate_queryset(completions)
        if page is not None:
            serializer = TaskCompletionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TaskCompletionSerializer(completions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get task statistics including recurring task stats.
        """
        queryset = self.get_queryset()
        recurring_tasks = queryset.filter(is_recurring=True)

        stats = {
            'total': queryset.count(),
            'todo': queryset.filter(status=Task.Status.TODO).count(),
            'in_progress': queryset.filter(status=Task.Status.IN_PROGRESS).count(),
            'completed': queryset.filter(status=Task.Status.COMPLETED).count(),
            'archived': queryset.filter(status=Task.Status.ARCHIVED).count(),
            'by_priority': {
                'low': queryset.filter(priority=Task.Priority.LOW).count(),
                'medium': queryset.filter(priority=Task.Priority.MEDIUM).count(),
                'high': queryset.filter(priority=Task.Priority.HIGH).count(),
                'urgent': queryset.filter(priority=Task.Priority.URGENT).count(),
            },
            'recurring': {
                'total': recurring_tasks.count(),
                'by_period': {
                    'daily': recurring_tasks.filter(recurrence_period=Task.RecurrencePeriod.DAILY).count(),
                    'weekly': recurring_tasks.filter(recurrence_period=Task.RecurrencePeriod.WEEKLY).count(),
                    'biweekly': recurring_tasks.filter(recurrence_period=Task.RecurrencePeriod.BIWEEKLY).count(),
                    'monthly': recurring_tasks.filter(recurrence_period=Task.RecurrencePeriod.MONTHLY).count(),
                    'quarterly': recurring_tasks.filter(recurrence_period=Task.RecurrencePeriod.QUARTERLY).count(),
                    'yearly': recurring_tasks.filter(recurrence_period=Task.RecurrencePeriod.YEARLY).count(),
                },
                'total_completions': TaskCompletion.objects.filter(task__in=recurring_tasks).count(),
            }
        }
        return Response(stats)

    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """
        Bulk update status for multiple tasks.

        Expected payload:
        {
            "task_ids": [1, 2, 3],
            "status": "completed"
        }
        """
        task_ids = request.data.get('task_ids', [])
        new_status = request.data.get('status')

        if not task_ids:
            return Response(
                {'error': 'No task IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status not in dict(Task.Status.choices):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated = self.get_queryset().filter(id__in=task_ids).update(status=new_status)

        return Response({
            'updated': updated,
            'message': f'Successfully updated {updated} tasks'
        })

    @action(detail=False, methods=['get'])
    def recurring(self, request):
        """
        Get only recurring tasks.
        """
        queryset = self.get_queryset().filter(is_recurring=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=SyncCompletionsSerializer,
        responses={200: SyncCompletionsResponseSerializer},
    )
    @action(detail=True, methods=['post'])
    def sync_completions(self, request, pk=None):
        """
        Synchronize completions for a recurring task.

        Accepts a list of dates. Compares with existing completions:
        - Adds new completions for dates not in DB
        - Removes completions for dates not in the list
        """
        from datetime import datetime as dt

        task = self.get_object()

        if not task.is_recurring:
            return Response(
                {'error': 'This action is only available for recurring tasks'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SyncCompletionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dates = serializer.validated_data['dates']
        completed_value = serializer.validated_data.get('completed_value')

        incoming_dates = set(dates)

        # Get existing completion dates
        existing_completions = task.completions.all()
        existing_dates = {}
        for completion in existing_completions:
            date = completion.completed_at.date()
            existing_dates[date] = completion

        existing_date_set = set(existing_dates.keys())

        # Dates to add (in incoming but not existing)
        dates_to_add = incoming_dates - existing_date_set

        # Dates to remove (in existing but not incoming)
        dates_to_remove = existing_date_set - incoming_dates

        added_count = 0
        removed_count = 0

        # Add new completions
        for date in dates_to_add:
            TaskCompletion.objects.create(
                task=task,
                completed_at=dt.combine(date, dt.min.time().replace(hour=12)),
                completed_value=completed_value,
                notes='',
            )
            added_count += 1

        # Remove completions
        for date in dates_to_remove:
            existing_dates[date].delete()
            removed_count += 1

        return Response({
            'added': added_count,
            'removed': removed_count,
            'total': len(incoming_dates),
            'task': TaskWithCompletionsSerializer(task).data,
        })


@extend_schema_view(
    list=extend_schema(tags=["Completions"]),
    create=extend_schema(tags=["Completions"]),
    retrieve=extend_schema(tags=["Completions"]),
    update=extend_schema(tags=["Completions"]),
    partial_update=extend_schema(tags=["Completions"]),
    destroy=extend_schema(tags=["Completions"]),
)
class TaskCompletionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task completions.

    Provides full CRUD access to completion records.
    """
    queryset = TaskCompletion.objects.all()
    serializer_class = TaskCompletionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TaskCompletionFilter
    ordering_fields = ['completed_at']
    ordering = ['-completed_at']

    def get_serializer_class(self):
        """Use different serializer for create/update."""
        if self.action in ['create', 'update', 'partial_update']:
            return TaskCompletionCreateSerializer
        return TaskCompletionSerializer

    def get_queryset(self):
        """Filter completions by user and optionally by task."""
        queryset = super().get_queryset()

        # Filter by authenticated user
        if self.request.user.is_authenticated:
            queryset = queryset.filter(task__user=self.request.user)
        else:
            queryset = queryset.none()

        # Additional filter by task_id if specified
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        return queryset
