"""
Tests for Task API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.tasks.models import Task


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def sample_task():
    """Create and return a sample task."""
    return Task.objects.create(
        title="Sample Task", description="Sample description", priority=Task.Priority.HIGH
    )


@pytest.mark.django_db
class TestTaskAPI:
    """Tests for Task API endpoints."""

    def test_list_tasks(self, api_client, sample_task):
        """Test listing all tasks."""
        url = reverse("tasks:task-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_create_task(self, api_client):
        """Test creating a new task."""
        url = reverse("tasks:task-list")
        data = {"title": "New Task", "description": "New task description", "priority": "high"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Task"
        assert Task.objects.filter(title="New Task").exists()

    def test_retrieve_task(self, api_client, sample_task):
        """Test retrieving a specific task."""
        url = reverse("tasks:task-detail", args=[sample_task.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == sample_task.title

    def test_update_task(self, api_client, sample_task):
        """Test updating a task."""
        url = reverse("tasks:task-detail", args=[sample_task.id])
        data = {
            "title": "Updated Task",
            "description": "Updated description",
            "priority": "low",
            "status": "in_progress",
        }
        response = api_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        sample_task.refresh_from_db()
        assert sample_task.title == "Updated Task"
        assert sample_task.status == Task.Status.IN_PROGRESS

    def test_partial_update_task(self, api_client, sample_task):
        """Test partial update of a task."""
        url = reverse("tasks:task-detail", args=[sample_task.id])
        data = {"priority": "urgent"}
        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        sample_task.refresh_from_db()
        assert sample_task.priority == Task.Priority.URGENT

    def test_delete_task(self, api_client, sample_task):
        """Test deleting a task."""
        url = reverse("tasks:task-detail", args=[sample_task.id])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Task.objects.filter(id=sample_task.id).exists()

    def test_complete_task(self, api_client, sample_task):
        """Test the complete action."""
        url = reverse("tasks:task-complete", args=[sample_task.id])
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        sample_task.refresh_from_db()
        assert sample_task.status == Task.Status.COMPLETED
        assert sample_task.completed_at is not None

    def test_update_status(self, api_client, sample_task):
        """Test the update_status action."""
        url = reverse("tasks:task-update-status", args=[sample_task.id])
        data = {"status": "in_progress"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        sample_task.refresh_from_db()
        assert sample_task.status == Task.Status.IN_PROGRESS

    def test_task_stats(self, api_client):
        """Test the stats endpoint."""
        Task.objects.create(title="Task 1", status=Task.Status.TODO)
        Task.objects.create(title="Task 2", status=Task.Status.COMPLETED)
        Task.objects.create(title="Task 3", status=Task.Status.IN_PROGRESS)

        url = reverse("tasks:task-stats")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "total" in response.data
        assert "todo" in response.data
        assert "completed" in response.data
        assert "in_progress" in response.data

    def test_filter_by_status(self, api_client):
        """Test filtering tasks by status."""
        Task.objects.create(title="Todo Task", status=Task.Status.TODO)
        Task.objects.create(title="Completed Task", status=Task.Status.COMPLETED)

        url = reverse("tasks:task-list")
        response = api_client.get(url, {"status": "todo"})

        assert response.status_code == status.HTTP_200_OK
        for task in response.data["results"]:
            assert task["status"] == "todo"

    def test_search_tasks(self, api_client):
        """Test searching tasks."""
        Task.objects.create(title="Python Learning", description="Learn Django")
        Task.objects.create(title="JavaScript Project", description="React app")

        url = reverse("tasks:task-list")
        response = api_client.get(url, {"search": "Python"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
        assert "Python" in response.data["results"][0]["title"]

    def test_create_task_empty_title(self, api_client):
        """Test that creating a task with empty title fails."""
        url = reverse("tasks:task-list")
        data = {"title": "", "description": "Some description"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBulkUpdateCompletions:
    """Tests for the bulk_update_completions action."""

    @pytest.fixture
    def recurring_task(self):
        return Task.objects.create(
            title="Daily push-ups",
            is_recurring=True,
            recurrence_period=Task.RecurrencePeriod.DAILY,
            recurrence_target_count=1,
        )

    def _url(self, task):
        return reverse(
            "tasks:task-bulk-update-completions", args=[task.id]
        )

    def test_additions_create_completions(self, api_client, recurring_task):
        from apps.tasks.models import TaskCompletion

        response = api_client.post(
            self._url(recurring_task),
            data={
                "additions": [
                    {"completed_at": "2026-04-01T10:00:00Z"},
                    {"completed_at": "2026-04-02T10:00:00Z", "notes": "easy"},
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["added"]) == 2
        assert response.data["removed_ids"] == []
        assert response.data["skipped_ids"] == []
        # Both new completions are persisted with returned IDs
        ids = [c["id"] for c in response.data["added"]]
        assert TaskCompletion.objects.filter(id__in=ids).count() == 2

    def test_removals_only_touch_listed_ids(self, api_client, recurring_task):
        """The classic regression: a sparse removal list MUST NOT delete
        completions the client did not name."""
        from apps.tasks.models import TaskCompletion
        from django.utils import timezone

        keep1 = TaskCompletion.objects.create(
            task=recurring_task, completed_at=timezone.now()
        )
        delete_me = TaskCompletion.objects.create(
            task=recurring_task, completed_at=timezone.now()
        )
        keep2 = TaskCompletion.objects.create(
            task=recurring_task, completed_at=timezone.now()
        )

        response = api_client.post(
            self._url(recurring_task),
            data={"removals": [delete_me.id]},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["removed_ids"] == [delete_me.id]
        assert response.data["skipped_ids"] == []
        assert TaskCompletion.objects.filter(id=keep1.id).exists()
        assert TaskCompletion.objects.filter(id=keep2.id).exists()
        assert not TaskCompletion.objects.filter(id=delete_me.id).exists()

    def test_cross_task_removal_is_skipped(self, api_client, recurring_task):
        """Sending a completion ID that belongs to *another* task must
        not delete it — id ends up in skipped_ids instead."""
        from apps.tasks.models import TaskCompletion
        from django.utils import timezone

        other_task = Task.objects.create(
            title="Other recurring",
            is_recurring=True,
            recurrence_period=Task.RecurrencePeriod.DAILY,
        )
        foreign = TaskCompletion.objects.create(
            task=other_task, completed_at=timezone.now()
        )

        response = api_client.post(
            self._url(recurring_task),
            data={"removals": [foreign.id]},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["removed_ids"] == []
        assert response.data["skipped_ids"] == [foreign.id]
        assert TaskCompletion.objects.filter(id=foreign.id).exists()

    def test_combined_add_and_remove_atomic(self, api_client, recurring_task):
        from apps.tasks.models import TaskCompletion
        from django.utils import timezone

        existing = TaskCompletion.objects.create(
            task=recurring_task, completed_at=timezone.now()
        )

        response = api_client.post(
            self._url(recurring_task),
            data={
                "additions": [{"completed_at": "2026-04-10T08:00:00Z"}],
                "removals": [existing.id],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["added"]) == 1
        assert response.data["removed_ids"] == [existing.id]
        assert not TaskCompletion.objects.filter(id=existing.id).exists()

    def test_rejects_non_recurring_task(self, api_client, sample_task):
        """sample_task is non-recurring; endpoint must reject."""
        response = api_client.post(
            self._url(sample_task),
            data={"additions": []},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_empty_payload_is_noop(self, api_client, recurring_task):
        from apps.tasks.models import TaskCompletion
        from django.utils import timezone

        TaskCompletion.objects.create(
            task=recurring_task, completed_at=timezone.now()
        )

        response = api_client.post(
            self._url(recurring_task), data={}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["added"] == []
        assert response.data["removed_ids"] == []
        assert response.data["skipped_ids"] == []
        assert (
            TaskCompletion.objects.filter(task=recurring_task).count() == 1
        )


