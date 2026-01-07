"""
Tests for Task models.
"""
import pytest
from django.utils import timezone

from apps.tasks.models import Task


@pytest.mark.django_db
class TestTaskModel:
    """Tests for the Task model."""

    def test_create_task(self):
        """Test creating a task with minimal fields."""
        task = Task.objects.create(title='Test Task')
        assert task.id is not None
        assert task.title == 'Test Task'
        assert task.status == Task.Status.TODO
        assert task.priority == Task.Priority.MEDIUM

    def test_task_str(self):
        """Test task string representation."""
        task = Task(title='My Task')
        assert str(task) == 'My Task'

    def test_mark_completed(self):
        """Test marking a task as completed."""
        task = Task.objects.create(title='Test Task')
        assert task.status == Task.Status.TODO
        assert task.completed_at is None

        task.mark_completed()

        task.refresh_from_db()
        assert task.status == Task.Status.COMPLETED
        assert task.completed_at is not None

    def test_is_overdue_true(self):
        """Test is_overdue property when task is overdue."""
        task = Task.objects.create(
            title='Overdue Task',
            due_date=timezone.now() - timezone.timedelta(days=1)
        )
        assert task.is_overdue is True

    def test_is_overdue_false_future_date(self):
        """Test is_overdue property when due date is in the future."""
        task = Task.objects.create(
            title='Future Task',
            due_date=timezone.now() + timezone.timedelta(days=1)
        )
        assert task.is_overdue is False

    def test_is_overdue_false_completed(self):
        """Test is_overdue property when task is completed."""
        task = Task.objects.create(
            title='Completed Task',
            due_date=timezone.now() - timezone.timedelta(days=1),
            status=Task.Status.COMPLETED
        )
        assert task.is_overdue is False

    def test_is_overdue_false_no_due_date(self):
        """Test is_overdue property when no due date is set."""
        task = Task.objects.create(title='No Due Date Task')
        assert task.is_overdue is False

    def test_tags_list(self):
        """Test tags_list property."""
        task = Task(title='Tagged Task', tags='python, django, rest')
        assert task.tags_list == ['python', 'django', 'rest']

    def test_tags_list_empty(self):
        """Test tags_list property when empty."""
        task = Task(title='Untagged Task', tags='')
        assert task.tags_list == []

    def test_timestamps_auto_created(self):
        """Test that timestamps are auto-created."""
        task = Task.objects.create(title='Test Task')
        assert task.created_at is not None
        assert task.updated_at is not None

