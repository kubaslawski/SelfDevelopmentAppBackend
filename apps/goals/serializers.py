"""
Serializers for Goals API.
"""

from rest_framework import serializers

from apps.groups.models import Group
from apps.tasks.models import Visibility

from .models import Goal, Milestone


class MilestoneSerializer(serializers.ModelSerializer):
    """Serializer for Milestone model."""

    progress_percentage = serializers.FloatField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    task_count = serializers.IntegerField(read_only=True)
    completed_task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Milestone
        fields = [
            "id",
            "goal",
            "title",
            "description",
            "status",
            "order",
            "target_date",
            "completed_at",
            "requirements",
            "success_criteria",
            "notes",
            "suggested_tasks",
            "progress_percentage",
            "days_remaining",
            "is_overdue",
            "task_count",
            "completed_task_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "completed_at", "created_at", "updated_at"]


class MilestoneCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating milestones."""

    class Meta:
        model = Milestone
        fields = [
            "title",
            "description",
            "order",
            "target_date",
            "requirements",
            "success_criteria",
            "suggested_tasks",
        ]


class GoalListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for goal lists."""

    progress_percentage = serializers.FloatField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    milestone_count = serializers.SerializerMethodField()
    visibility = serializers.ChoiceField(choices=Visibility.choices, read_only=True)

    class Meta:
        model = Goal
        fields = [
            "id",
            "title",
            "description",
            "category",
            "icon",
            "status",
            "start_date",
            "target_date",
            "progress_percentage",
            "days_remaining",
            "is_overdue",
            "milestone_count",
            "visibility",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "icon", "created_at", "updated_at"]

    def get_milestone_count(self, obj) -> int:
        return obj.milestones.count()


class GoalDetailSerializer(serializers.ModelSerializer):
    """Full serializer for goal details including milestones."""

    milestones = MilestoneSerializer(many=True, read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    # Visibility fields
    visibility = serializers.ChoiceField(
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    shared_with_groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        required=False,
    )
    shared_with_group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Goal
        fields = [
            "id",
            "title",
            "description",
            "category",
            "status",
            "start_date",
            "target_date",
            "completed_at",
            "planning_answers",
            "planning_questions",
            "llm_generated_plan",
            "plan_generated_at",
            "motivation",
            "potential_obstacles",
            "tips",
            "final_achievement",
            "icon",
            "milestones",
            "progress_percentage",
            "days_remaining",
            "is_overdue",
            # Visibility
            "visibility",
            "shared_with_groups",
            "shared_with_group_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "completed_at",
            "llm_generated_plan",
            "plan_generated_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """Validate visibility with shared_with_groups."""
        visibility = data.get("visibility", getattr(self.instance, "visibility", Visibility.PRIVATE) if self.instance else Visibility.PRIVATE)
        shared_with_group_ids = data.get("shared_with_group_ids", [])
        
        if visibility == Visibility.GROUP and not shared_with_group_ids:
            if not (self.instance and self.instance.shared_with_groups.exists()):
                raise serializers.ValidationError(
                    {"shared_with_group_ids": "At least one group is required when visibility is 'group'."}
                )
        return data

    def update(self, instance, validated_data):
        """Update goal with shared_with_groups handling."""
        shared_with_group_ids = validated_data.pop("shared_with_group_ids", None)
        shared_with_groups = validated_data.pop("shared_with_groups", None)
        
        instance = super().update(instance, validated_data)
        
        if shared_with_group_ids is not None:
            groups = Group.objects.filter(id__in=shared_with_group_ids)
            instance.shared_with_groups.set(groups)
        elif shared_with_groups is not None:
            instance.shared_with_groups.set(shared_with_groups)
        
        return instance


class GoalCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new goal.

    Step 1 of the flow: User just provides their goal description.
    The system will then generate contextual questions.
    """
    
    # Visibility fields
    visibility = serializers.ChoiceField(
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
        required=False,
    )
    shared_with_group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Goal
        fields = [
            "id",
            "title",
            "description",
            "category",
            "target_date",
            "icon",
            "status",
            "visibility",
            "shared_with_group_ids",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, data):
        """Validate visibility with shared_with_groups."""
        visibility = data.get("visibility", Visibility.PRIVATE)
        shared_with_group_ids = data.get("shared_with_group_ids", [])
        
        if visibility == Visibility.GROUP and not shared_with_group_ids:
            raise serializers.ValidationError(
                {"shared_with_group_ids": "At least one group is required when visibility is 'group'."}
            )
        return data

    def create(self, validated_data):
        shared_with_group_ids = validated_data.pop("shared_with_group_ids", [])
        
        validated_data["user"] = self.context["request"].user
        validated_data["status"] = Goal.Status.DRAFT
        goal = super().create(validated_data)
        
        if shared_with_group_ids:
            groups = Group.objects.filter(id__in=shared_with_group_ids)
            goal.shared_with_groups.set(groups)
        
        return goal


# =============================================================================
# Dynamic Question Flow Serializers
# =============================================================================

class GenerateQuestionsSerializer(serializers.Serializer):
    """
    Serializer for requesting LLM-generated questions.

    Step 2: Based on the goal, generate contextual questions.
    """

    # No input needed - questions are generated based on goal.title/description
    pass


class QuestionAnswerSerializer(serializers.Serializer):
    """A single question-answer pair."""

    question_id = serializers.CharField(
        help_text="The ID of the question being answered",
    )
    question = serializers.CharField(
        help_text="The question text (for context)",
    )
    answer = serializers.CharField(
        help_text="User's answer to the question",
        allow_blank=True,
    )


class SubmitAnswersSerializer(serializers.Serializer):
    """
    Serializer for submitting answers to generated questions.

    Step 3: User submits answers, system generates the plan.
    """

    answers = QuestionAnswerSerializer(
        many=True,
        help_text="List of question-answer pairs",
    )


class GeneratedQuestionSerializer(serializers.Serializer):
    """Serializer for a single generated question."""

    id = serializers.CharField()
    question = serializers.CharField()
    type = serializers.ChoiceField(
        choices=["text", "choice", "number"],
        default="text",
    )
    placeholder = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    options = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Options for 'choice' type questions",
    )


class GeneratedQuestionsResponseSerializer(serializers.Serializer):
    """Response serializer for generated questions endpoint."""

    questions = GeneratedQuestionSerializer(many=True)


# =============================================================================
# Plan Generation Serializers
# =============================================================================

class GeneratedTaskSerializer(serializers.Serializer):
    """Serializer for a task in the generated plan."""

    title = serializers.CharField()
    description = serializers.CharField()
    estimated_duration = serializers.CharField()
    priority = serializers.ChoiceField(choices=["high", "medium", "low"])
    is_recurring = serializers.BooleanField(default=False)
    recurrence_period = serializers.CharField(
        required=False,
        allow_null=True,
    )
    category = serializers.ChoiceField(
        choices=["preparation", "learning", "practice", "review", "achievement"],
        default="learning",
    )


class GeneratedMilestoneSerializer(serializers.Serializer):
    """Serializer for a milestone in the generated plan."""

    title = serializers.CharField()
    description = serializers.CharField()
    target_date = serializers.DateField()
    requirements = serializers.CharField(required=False, allow_blank=True)
    success_criteria = serializers.CharField(required=False, allow_blank=True)
    tasks = GeneratedTaskSerializer(many=True)


class GeneratedPlanSerializer(serializers.Serializer):
    """Serializer for the LLM-generated plan response."""

    summary = serializers.CharField()
    milestones = GeneratedMilestoneSerializer(many=True)
    tips = serializers.ListField(child=serializers.CharField())
    potential_obstacles = serializers.ListField(child=serializers.CharField())
    motivation = serializers.CharField()
    final_achievement = serializers.CharField(required=False, allow_blank=True)
