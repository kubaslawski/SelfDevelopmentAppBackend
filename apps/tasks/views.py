"""
Views for the Tasks app.
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import TaskFilter, TaskCompletionFilter
from .models import Task, TaskCompletion
from .serializers import (
    TaskCompletionCreateSerializer,
    TaskCompletionSerializer,
    TaskListSerializer,
    TaskSerializer,
    TaskStatusUpdateSerializer,
    TaskWithCompletionsSerializer,
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
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
        Optionally filter tasks by user if authenticated.
        """
        queryset = super().get_queryset()
        # Uncomment below to filter by authenticated user
        # if self.request.user.is_authenticated:
        #     queryset = queryset.filter(user=self.request.user)
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


class TaskCompletionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing task completions.
    
    Provides read-only access to completion records.
    """
    queryset = TaskCompletion.objects.all()
    serializer_class = TaskCompletionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TaskCompletionFilter
    ordering_fields = ['completed_at']
    ordering = ['-completed_at']

    def get_queryset(self):
        """Filter completions by task if specified."""
        queryset = super().get_queryset()
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        return queryset
