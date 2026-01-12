"""
Serializers for the Tasks app.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Task, TaskCompletion


class TaskCompletionSerializer(serializers.ModelSerializer):
    """
    Serializer for TaskCompletion model.
    """

    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = TaskCompletion
        fields = [
            "id",
            "task",
            "task_title",
            "completed_at",
            "completed_value",
            "notes",
            "duration_minutes",
        ]
        read_only_fields = ["id", "completed_at"]


class TaskCompletionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a TaskCompletion.
    """

    completed_at = serializers.DateTimeField(required=False, allow_null=True)
    completed_value = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )

    class Meta:
        model = TaskCompletion
        fields = [
            "completed_at",
            "completed_value",
            "notes",
            "duration_minutes",
        ]


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model - full CRUD operations.
    """

    # Override status to return None for recurring tasks (their status is determined by completions)
    status = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    tags_list = serializers.ListField(child=serializers.CharField(), read_only=True)
    recurrence_display = serializers.CharField(read_only=True, allow_null=True)
    goal_display = serializers.CharField(read_only=True, allow_null=True)
    unit_display_name = serializers.CharField(read_only=True, allow_null=True)
    target_in_minutes = serializers.IntegerField(read_only=True, allow_null=True)
    completions_in_current_period = serializers.IntegerField(read_only=True)
    completed_value_in_current_period = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    is_period_complete = serializers.BooleanField(read_only=True)
    remaining_completions_in_period = serializers.IntegerField(read_only=True)
    last_completion = serializers.DateTimeField(read_only=True, allow_null=True)
    current_period_start = serializers.DateTimeField(read_only=True, allow_null=True)
    current_period_end = serializers.DateTimeField(read_only=True, allow_null=True)
    total_completions = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "completed_at",
            # Recurrence fields
            "is_recurring",
            "recurrence_period",
            "recurrence_target_count",
            "recurrence_end_date",
            # Computed recurrence fields
            "recurrence_display",
            "current_period_start",
            "current_period_end",
            "completions_in_current_period",
            "completed_value_in_current_period",
            "is_period_complete",
            "remaining_completions_in_period",
            "last_completion",
            "total_completions",
            # Goal/target fields
            "unit_type",
            "custom_unit_name",
            "target_value",
            "goal_display",
            "unit_display_name",
            "target_in_minutes",
            # Other fields
            "estimated_duration",
            "tags",
            "tags_list",
            "is_overdue",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "completed_at", "created_at", "updated_at"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_status(self, obj) -> Optional[str]:
        """Return status for non-recurring tasks, None for recurring tasks."""
        if obj.is_recurring:
            return None
        return obj.status

    @extend_schema_field(serializers.IntegerField())
    def get_total_completions(self, obj) -> int:
        """Get total number of completions for recurring tasks."""
        if obj.is_recurring:
            return obj.completions.count()
        return 1 if obj.status == Task.Status.COMPLETED else 0

    def validate_title(self, value):
        """Validate that title is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()

    def validate_estimated_duration(self, value):
        """Validate that estimated duration is positive."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Estimated duration must be positive.")
        return value

    def validate(self, data):
        """Validate recurrence fields."""
        is_recurring = data.get("is_recurring", getattr(self.instance, "is_recurring", False))

        if is_recurring:
            recurrence_period = data.get(
                "recurrence_period", getattr(self.instance, "recurrence_period", None)
            )
            if not recurrence_period:
                raise serializers.ValidationError(
                    {"recurrence_period": "Recurrence period is required for recurring tasks."}
                )

        return data


class TaskListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing tasks.
    """

    # Override status to return None for recurring tasks (their status is determined by completions)
    status = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    is_period_complete = serializers.BooleanField(read_only=True)
    goal_display = serializers.CharField(read_only=True, allow_null=True)
    unit_display_name = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "completed_at",
            "is_recurring",
            "recurrence_period",
            "recurrence_target_count",
            "is_overdue",
            "is_period_complete",
            # Goal/target fields
            "unit_type",
            "custom_unit_name",
            "target_value",
            "goal_display",
            "unit_display_name",
            "created_at",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_status(self, obj) -> Optional[str]:
        """Return status for non-recurring tasks, None for recurring tasks."""
        if obj.is_recurring:
            return None
        return obj.status


class TaskWithCompletionsSerializer(TaskSerializer):
    """
    Task serializer that includes recent completions.
    """

    recent_completions = serializers.SerializerMethodField()

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ["recent_completions"]

    @extend_schema_field(TaskCompletionSerializer(many=True))
    def get_recent_completions(self, obj) -> list:
        """Get the 10 most recent completions."""
        if not obj.is_recurring:
            return []
        completions = obj.completions.order_by("-completed_at")[:10]
        return TaskCompletionSerializer(completions, many=True).data


class TaskStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating task status.
    Only for non-recurring tasks - recurring tasks don't have status.
    """

    status = serializers.ChoiceField(choices=Task.Status.choices)

    def validate(self, data):
        """Prevent status updates for recurring tasks."""
        if self.instance and self.instance.is_recurring:
            raise serializers.ValidationError(
                "Cannot update status for recurring tasks. "
                "Their completion status is determined by completions in the current period."
            )
        return data

    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        if validated_data["status"] == Task.Status.COMPLETED:
            instance.mark_completed()
        else:
            instance.save(update_fields=["status", "updated_at"])
        return instance


class SyncCompletionsSerializer(serializers.Serializer):
    """
    Serializer for syncing completions.
    Accepts a list of dates and an optional completed_value.
    """

    dates = serializers.ListField(
        child=serializers.DateField(),
        help_text="List of dates (YYYY-MM-DD) for completions",
    )
    completed_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Default completed value for new completions",
    )


class SyncCompletionsResponseSerializer(serializers.Serializer):
    """
    Response serializer for sync_completions endpoint.
    """

    added = serializers.IntegerField(help_text="Number of completions added")
    removed = serializers.IntegerField(help_text="Number of completions removed")
    total = serializers.IntegerField(help_text="Total completions after sync")
    task = TaskWithCompletionsSerializer()
