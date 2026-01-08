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
