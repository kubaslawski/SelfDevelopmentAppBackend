"""
Admin configuration for the Tasks app.
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Task, TaskCompletion


class TaskCompletionInline(admin.TabularInline):
    """Inline admin for TaskCompletion."""
    model = TaskCompletion
    extra = 0
    readonly_fields = ['completed_at']
    fields = ['completed_at', 'completed_value', 'notes', 'duration_minutes']
    ordering = ['-completed_at']

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model."""

    list_display = [
        'id',
        'title',
        'status_badge',
        'priority_badge',
        'goal_badge',
        'recurrence_badge',
        'due_date',
        'is_overdue_display',
        'completions_display',
        'user',
        'created_at',
    ]
    list_filter = [
        'status',
        'priority',
        'unit_type',
        'is_recurring',
        'recurrence_period',
        'created_at',
        'due_date',
    ]
    search_fields = ['title', 'description', 'tags']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'completions_summary']
    date_hierarchy = 'created_at'
    list_per_page = 25
    inlines = [TaskCompletionInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Goal / Target', {
            'fields': ('unit_type', 'custom_unit_name', 'target_value'),
            'description': 'Set a measurable goal. Use "Custom unit" and fill custom_unit_name for your own units (e.g., pages, liters).'
        }),
        ('Recurrence Settings', {
            'fields': (
                'is_recurring',
                'recurrence_period',
                'recurrence_target_count',
                'recurrence_end_date',
                'completions_summary',
            ),
            'classes': ('collapse',),
            'description': 'Configure recurring task settings. Periods always start from calendar boundaries (1st of month, Monday of week, etc.).'
        }),
        ('Dates', {
            'fields': ('due_date', 'estimated_duration')
        }),
        ('Metadata', {
            'fields': ('tags', 'user')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Display status as a colored badge."""
        colors = {
            'todo': '#6c757d',
            'in_progress': '#007bff',
            'completed': '#28a745',
            'archived': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def priority_badge(self, obj):
        """Display priority as a colored badge."""
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'urgent': '#dc3545',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'

    def goal_badge(self, obj):
        """Display goal/target as a badge."""
        if not obj.goal_display:
            return '-'

        # Different colors for different unit types
        colors = {
            'minutes': '#6f42c1',  # Purple for time
            'hours': '#6f42c1',    # Purple for time
            'count': '#20c997',    # Teal for count
        }
        icons = {
            'minutes': '⏱',
            'hours': '⏱',
            'count': '🔢',
        }
        color = colors.get(obj.unit_type, '#6c757d')
        icon = icons.get(obj.unit_type, '🎯')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            color, icon, obj.goal_display
        )
    goal_badge.short_description = 'Goal'

    def recurrence_badge(self, obj):
        """Display recurrence info as a badge."""
        if not obj.is_recurring:
            return '-'

        display = obj.recurrence_display or 'Recurring'
        return format_html(
            '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">🔄 {}</span>',
            display
        )
    recurrence_badge.short_description = 'Recurrence'

    def is_overdue_display(self, obj):
        """Display overdue status."""
        if obj.is_overdue:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠ Overdue</span>'
            )
        return '-'
    is_overdue_display.short_description = 'Overdue'

    def completions_display(self, obj):
        """Display completion count for recurring tasks."""
        if not obj.is_recurring:
            return '-'

        current = obj.completions_in_current_period
        target = obj.recurrence_target_count or 1
        total = obj.completions.count()

        if current >= target:
            color = '#28a745'
            icon = '✓'
        else:
            color = '#ffc107'
            icon = '○'

        return format_html(
            '<span style="color: {};">{} {}/{} (total: {})</span>',
            color, icon, current, target, total
        )
    completions_display.short_description = 'Completions'

    def completions_summary(self, obj):
        """Detailed completions summary for the detail view."""
        if not obj.is_recurring:
            return 'This is not a recurring task.'

        current = obj.completions_in_current_period
        target = obj.recurrence_target_count or 1
        remaining = obj.remaining_completions_in_period
        total = obj.completions.count()
        last = obj.last_completion
        period_start = obj.current_period_start
        period_end = obj.current_period_end

        last_str = last.strftime('%Y-%m-%d %H:%M') if last else 'Never'
        period_start_str = period_start.strftime('%Y-%m-%d %H:%M') if period_start else '-'
        period_end_str = period_end.strftime('%Y-%m-%d %H:%M') if period_end else '-'

        return format_html(
            '<strong>Current period:</strong> {} to {}<br>'
            '<strong>Progress:</strong> {}/{} completions<br>'
            '<strong>Remaining:</strong> {}<br>'
            '<strong>Total completions:</strong> {}<br>'
            '<strong>Last completion:</strong> {}',
            period_start_str, period_end_str,
            current, target, remaining, total, last_str
        )
    completions_summary.short_description = 'Completions Summary'

    actions = ['mark_completed', 'mark_archived', 'record_completion']

    @admin.action(description='Mark selected tasks as completed')
    def mark_completed(self, request, queryset):
        for task in queryset:
            task.mark_completed()
        self.message_user(request, f'{queryset.count()} tasks marked as completed.')

    @admin.action(description='Mark selected tasks as archived')
    def mark_archived(self, request, queryset):
        count = queryset.update(status=Task.Status.ARCHIVED)
        self.message_user(request, f'{count} tasks marked as archived.')

    @admin.action(description='Record completion for recurring tasks')
    def record_completion(self, request, queryset):
        count = 0
        for task in queryset.filter(is_recurring=True):
            TaskCompletion.objects.create(task=task)
            count += 1
        self.message_user(request, f'Recorded {count} completions for recurring tasks.')


@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    """Admin interface for TaskCompletion model."""

    list_display = [
        'id',
        'task_link',
        'completed_at',
        'completed_value',
        'duration_minutes',
        'notes_preview',
    ]
    list_filter = [
        'completed_at',
        'task__recurrence_period',
    ]
    search_fields = ['task__title', 'notes']
    ordering = ['-completed_at']
    readonly_fields = ['completed_at']

    fieldsets = (
        ('Completion Info', {
            'fields': ('task', 'completed_at')
        }),
        ('Details', {
            'fields': ('completed_value', 'duration_minutes', 'notes'),
            'description': 'completed_value stores the numeric value in the task\'s unit type'
        }),
    )
    date_hierarchy = 'completed_at'
    list_per_page = 50
    raw_id_fields = ['task']

    def task_link(self, obj):
        """Display task as a link."""
        url = reverse('admin:tasks_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'
    task_link.admin_order_field = 'task__title'

    def notes_preview(self, obj):
        """Display truncated notes."""
        if obj.notes:
            return obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
        return '-'
    notes_preview.short_description = 'Notes'
