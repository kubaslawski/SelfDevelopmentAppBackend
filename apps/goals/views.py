"""
Views for Goals API.

Flow for creating a goal with AI-generated plan:
1. POST /goals/ - Create goal with title, description, target_date
2. POST /goals/{id}/generate_questions/ - LLM generates contextual questions
3. POST /goals/{id}/submit_answers/ - User submits answers, LLM generates plan
4. POST /goals/{id}/apply_plan/ - Create Milestone objects from plan
"""

import logging
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from core.llm import RateLimitExceeded
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tasks.models import Task

from .domain.dto import (
    ApplyPlanRequestDTO,
    GenerateQuestionsRequestDTO,
    LLMGeneratedPlanDTO,
    TaskInputDTO,
)
from .domain.entities import QuestionAnswer
from .models import Goal, Milestone, MilestoneTaskLink
from .serializers import (
    GoalCreateSerializer,
    GoalDetailSerializer,
    GoalListSerializer,
    MilestoneSerializer,
    SubmitAnswersSerializer,
)
from .services import (
    generate_plan,
    generate_questions,
    save_plan,
    save_questions,
)

logger = logging.getLogger(__name__)


# Priority weights for due date distribution (higher = gets more time earlier)
PRIORITY_WEIGHTS = {
    "high": 1,  # First in the milestone
    "medium": 2,  # Middle
    "low": 3,  # Later
}


def calculate_task_due_dates(
    tasks: List,
    milestone_start: date,
    milestone_end: date,
) -> List[Optional[date]]:
    """
    Calculate due dates for tasks within a milestone timeframe.

    Tasks are distributed across the milestone period based on priority:
    - High priority tasks get earlier due dates
    - Medium priority tasks get middle due dates
    - Low priority tasks get later due dates

    Recurring tasks don't get due dates (they repeat throughout).

    Args:
        tasks: List of task DTOs with priority and is_recurring attributes
        milestone_start: Start date of the milestone
        milestone_end: End date (target_date) of the milestone

    Returns:
        List of due dates (or None for recurring tasks) in the same order as input
    """
    if not tasks:
        return []

    # Filter out recurring tasks for due date calculation
    non_recurring_indices = [
        i for i, t in enumerate(tasks) if not getattr(t, "is_recurring", False)
    ]

    if not non_recurring_indices:
        # All tasks are recurring, no due dates needed
        return [None] * len(tasks)

    # Calculate available days
    total_days = (milestone_end - milestone_start).days
    if total_days <= 0:
        total_days = 7  # Default to 7 days if dates are invalid

    # Sort non-recurring tasks by priority (high first)
    sorted_indices = sorted(
        non_recurring_indices,
        key=lambda i: PRIORITY_WEIGHTS.get(getattr(tasks[i], "priority", "medium"), 2),
    )

    # Calculate due dates - distribute evenly across the milestone period
    num_tasks = len(sorted_indices)
    days_per_task = max(1, total_days // num_tasks)

    # Create result list with None for recurring tasks
    due_dates: List[Optional[date]] = [None] * len(tasks)

    for position, task_idx in enumerate(sorted_indices):
        # Calculate the day offset based on position
        day_offset = min((position + 1) * days_per_task, total_days)
        due_date = milestone_start + timedelta(days=day_offset)

        # Don't exceed milestone end date
        if due_date > milestone_end:
            due_date = milestone_end

        due_dates[task_idx] = due_date

    return due_dates


@extend_schema_view(
    list=extend_schema(tags=["Goals"]),
    create=extend_schema(tags=["Goals"]),
    retrieve=extend_schema(tags=["Goals"]),
    update=extend_schema(tags=["Goals"]),
    partial_update=extend_schema(tags=["Goals"]),
    destroy=extend_schema(tags=["Goals"]),
    generate_questions=extend_schema(tags=["Goals"]),
    submit_answers=extend_schema(tags=["Goals"]),
    apply_plan=extend_schema(tags=["Goals"]),
    complete=extend_schema(tags=["Goals"]),
    pause=extend_schema(tags=["Goals"]),
    resume=extend_schema(tags=["Goals"]),
    abandon=extend_schema(tags=["Goals"]),
)
class GoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Goals.

    Provides CRUD operations plus custom actions for:
    - Generating contextual questions (LLM)
    - Submitting answers and generating plan (LLM)
    - Applying generated plan (creating milestones)
    """

    permission_classes = [IsAuthenticated]
    queryset = Goal.objects.none()  # Default for schema generation

    def get_queryset(self):
        """Filter goals to current user only."""
        if getattr(self, "swagger_fake_view", False):
            return Goal.objects.none()
        return Goal.objects.filter(user=self.request.user).prefetch_related("milestones")

    def get_serializer_class(self):
        if self.action == "list":
            return GoalListSerializer
        elif self.action == "create":
            return GoalCreateSerializer
        elif self.action == "submit_answers":
            return SubmitAnswersSerializer
        return GoalDetailSerializer

    # =========================================================================
    # Step 2: Generate contextual questions
    # =========================================================================

    @action(detail=True, methods=["post"])
    def generate_questions(self, request, pk=None):
        """
        Generate contextual questions for the goal using LLM.

        The LLM analyzes the goal description and generates 3-5 specific
        questions that will help create a personalized plan.

        Returns:
            List of generated questions with id, question, type, placeholder.
        """
        goal = self.get_object()

        # Parse request
        request_dto = GenerateQuestionsRequestDTO.model_validate(request.data or {})

        # Don't regenerate if already has questions and user didn't force
        if goal.planning_questions and not request_dto.force:
            return Response(
                {
                    "success": True,
                    "questions": goal.planning_questions,
                    "cached": True,
                }
            )

        questions, is_fallback = generate_questions(goal=goal, user_id=request.user.id)
        save_questions(goal, questions)

        return Response(
            {
                "success": True,
                "questions": [
                    {
                        "id": q.id,
                        "question": q.question,
                        "type": q.type,
                        "placeholder": q.placeholder,
                        "options": q.options,
                    }
                    for q in questions
                ],
                "cached": False,
                "fallback": is_fallback,
            }
        )

    # =========================================================================
    # Step 3: Submit answers and generate plan
    # =========================================================================

    @action(detail=True, methods=["post"])
    def submit_answers(self, request, pk=None):
        """
        Submit answers to questions and generate the goal plan.

        This takes the user's answers and generates a complete plan with
        milestones and tasks using the LLM.

        Request body:
            {
                "answers": [
                    {"question_id": "q1", "question": "...", "answer": "..."},
                    {"question_id": "q2", "question": "...", "answer": "..."}
                ]
            }

        Returns:
            The generated plan with milestones, tips, and motivation.
        """
        goal = self.get_object()

        # Validate input
        serializer = SubmitAnswersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data["answers"]
        num_milestones = serializer.validated_data.get("num_milestones", 5)
        tasks_per_milestone = serializer.validated_data.get("tasks_per_milestone", 3)

        # Update goal status to planning
        goal.status = Goal.Status.PLANNING
        goal.planning_answers = answers
        goal.save(update_fields=["status", "planning_answers", "updated_at"])

        try:
            # Map answers to entities
            answer_entities = [
                QuestionAnswer(
                    question_id=a["question_id"],
                    question=a["question"],
                    answer=a["answer"],
                )
                for a in answers
            ]

            plan = generate_plan(
                goal=goal,
                answers=answer_entities,
                user_id=request.user.id,
                num_milestones=num_milestones,
                tasks_per_milestone=tasks_per_milestone,
            )
            save_plan(goal, plan)

            return Response(
                {
                    "success": True,
                    "plan": goal.llm_generated_plan,
                    "message": "Plan generated successfully. Review and apply when ready.",
                }
            )

        except RateLimitExceeded as e:
            goal.status = Goal.Status.DRAFT
            goal.save(update_fields=["status", "updated_at"])
            return Response(
                {
                    "success": False,
                    "error": "rate_limit_exceeded",
                    "message": str(e),
                    "retry_after": e.retry_after,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        except Exception as e:
            logger.error("Error generating plan for goal %s: %s", goal.id, e)
            goal.status = Goal.Status.DRAFT
            goal.save(update_fields=["status", "updated_at"])
            return Response(
                {
                    "success": False,
                    "error": "llm_error",
                    "message": "Failed to generate plan. Please try again later.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    # =========================================================================
    # Step 4: Apply the plan
    # =========================================================================

    @action(detail=True, methods=["post"])
    def apply_plan(self, request, pk=None):
        """
        Apply the generated plan by creating Milestone objects.

        This takes the LLM-generated plan stored in the goal and creates
        actual Milestone objects from it. User can optionally modify
        the milestones before applying.

        Request body (optional):
            {
                "milestones": [...]  // Override generated milestones
            }

        Returns:
            The updated goal with created milestones.
        """
        goal = self.get_object()

        if not goal.llm_generated_plan:
            return Response(
                {
                    "success": False,
                    "error": "no_plan",
                    "message": "No plan has been generated yet. Generate a plan first.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse and validate request using Pydantic DTO
        try:
            request_dto = ApplyPlanRequestDTO.model_validate(request.data)
        except PydanticValidationError as e:
            return Response(
                {
                    "success": False,
                    "error": "validation_error",
                    "message": "Invalid request data",
                    "details": e.errors(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use provided milestones or fall back to LLM-generated ones
        if request_dto.milestones:
            milestones_dtos = request_dto.milestones
        else:
            # Parse LLM-generated plan into DTO
            plan_dto = LLMGeneratedPlanDTO.model_validate(goal.llm_generated_plan)
            milestones_dtos = plan_dto.milestones

        if not milestones_dtos:
            return Response(
                {
                    "success": False,
                    "error": "no_milestones",
                    "message": "No milestones in the plan.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete existing milestones (and their task links) if any
        goal.milestones.all().delete()

        # Create milestones and tasks from plan using DTOs
        created_milestones = []
        total_tasks_created = 0

        # Calculate milestone start dates for due date distribution
        goal_start = goal.start_date or timezone.now().date()
        previous_milestone_end: Optional[date] = None

        for idx, milestone_dto in enumerate(milestones_dtos):
            # Parse milestone target date
            milestone_target = milestone_dto.target_date
            if isinstance(milestone_target, str):
                milestone_target = date.fromisoformat(milestone_target)

            # Determine milestone start date
            if previous_milestone_end:
                milestone_start = previous_milestone_end + timedelta(days=1)
            else:
                milestone_start = goal_start

            milestone = Milestone.objects.create(
                goal=goal,
                title=milestone_dto.title,
                description=milestone_dto.description,
                order=idx,
                target_date=milestone_target,
                requirements=milestone_dto.requirements,
                success_criteria=milestone_dto.success_criteria,
                suggested_tasks=[task.model_dump() for task in milestone_dto.tasks],
                status=Milestone.Status.PENDING,
            )
            created_milestones.append(milestone)

            # Calculate due dates for tasks in this milestone
            task_due_dates = calculate_task_due_dates(
                tasks=milestone_dto.tasks,
                milestone_start=milestone_start,
                milestone_end=milestone_target,
            )

            # Auto-create Task objects from tasks DTOs with calculated due dates
            for task_idx, task_dto in enumerate(milestone_dto.tasks):
                task_due_date = task_due_dates[task_idx] if task_idx < len(task_due_dates) else None

                # Convert date to datetime (model expects DateTimeField)
                task_due_datetime = (
                    timezone.make_aware(datetime.combine(task_due_date, time(23, 59)))
                    if task_due_date
                    else None
                )

                task = Task.objects.create(
                    user=request.user,
                    goal=goal,  # Link to goal for CASCADE delete
                    title=task_dto.title,
                    description=task_dto.description,
                    priority=task_dto.priority,
                    is_recurring=task_dto.is_recurring,
                    recurrence_period=task_dto.recurrence_period,
                    recurrence_target_count=1 if task_dto.is_recurring else None,
                    due_date=task_due_datetime,  # Set calculated due date as datetime
                    status=Task.Status.TODO,
                )
                MilestoneTaskLink.objects.create(
                    milestone=milestone,
                    task=task,
                )
                total_tasks_created += 1

            # Update for next iteration
            previous_milestone_end = milestone_target

        # Activate the goal
        goal.status = Goal.Status.ACTIVE
        if not goal.start_date:
            goal.start_date = timezone.now().date()
        goal.save(update_fields=["status", "start_date", "updated_at"])

        return Response(
            {
                "success": True,
                "message": f"Plan applied with {len(created_milestones)} milestones and {total_tasks_created} tasks.",
                "goal": GoalDetailSerializer(goal).data,
            }
        )

    # =========================================================================
    # Goal lifecycle actions
    # =========================================================================

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark the goal as completed."""
        goal = self.get_object()
        goal.status = Goal.Status.COMPLETED
        goal.completed_at = timezone.now()
        goal.save(update_fields=["status", "completed_at", "updated_at"])

        return Response(
            {
                "success": True,
                "message": "Congratulations! Goal marked as completed.",
                "goal": GoalDetailSerializer(goal).data,
            }
        )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause the goal."""
        goal = self.get_object()
        goal.status = Goal.Status.PAUSED
        goal.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "success": True,
                "goal": GoalDetailSerializer(goal).data,
            }
        )

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """Resume a paused goal."""
        goal = self.get_object()
        goal.status = Goal.Status.ACTIVE
        goal.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "success": True,
                "goal": GoalDetailSerializer(goal).data,
            }
        )

    @action(detail=True, methods=["post"])
    def abandon(self, request, pk=None):
        """Abandon the goal."""
        goal = self.get_object()
        goal.status = Goal.Status.ABANDONED
        goal.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "success": True,
                "goal": GoalDetailSerializer(goal).data,
            }
        )


@extend_schema_view(
    list=extend_schema(tags=["Goals"]),
    create=extend_schema(tags=["Goals"]),
    retrieve=extend_schema(tags=["Goals"]),
    update=extend_schema(tags=["Goals"]),
    partial_update=extend_schema(tags=["Goals"]),
    destroy=extend_schema(tags=["Goals"]),
    complete=extend_schema(tags=["Goals"]),
    start=extend_schema(tags=["Goals"]),
    skip=extend_schema(tags=["Goals"]),
    uncomplete=extend_schema(tags=["Goals"]),
    create_tasks=extend_schema(tags=["Goals"]),
)
class MilestoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Milestones.

    Milestones are always accessed in context of a Goal.
    """

    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]
    queryset = Milestone.objects.none()  # Default for schema generation

    def get_queryset(self):
        """Filter milestones to current user's goals only."""
        if getattr(self, "swagger_fake_view", False):
            return Milestone.objects.none()
        return Milestone.objects.filter(goal__user=self.request.user).select_related("goal")

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark the milestone as completed."""
        milestone = self.get_object()
        milestone.mark_completed()

        return Response(
            {
                "success": True,
                "milestone": MilestoneSerializer(milestone).data,
            }
        )

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """Start working on the milestone."""
        milestone = self.get_object()
        milestone.status = Milestone.Status.IN_PROGRESS
        milestone.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "success": True,
                "milestone": MilestoneSerializer(milestone).data,
            }
        )

    @action(detail=True, methods=["post"])
    def skip(self, request, pk=None):
        """Skip this milestone."""
        milestone = self.get_object()
        milestone.status = Milestone.Status.SKIPPED
        milestone.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "success": True,
                "milestone": MilestoneSerializer(milestone).data,
            }
        )

    @action(detail=True, methods=["post"])
    def uncomplete(self, request, pk=None):
        """Reopen a completed milestone back to pending."""
        milestone = self.get_object()
        milestone.status = Milestone.Status.PENDING
        milestone.completed_at = None
        milestone.save(update_fields=["status", "completed_at", "updated_at"])

        return Response(
            {
                "success": True,
                "milestone": MilestoneSerializer(milestone).data,
            }
        )

    @action(detail=True, methods=["post"])
    def create_tasks(self, request, pk=None):
        """
        Create actual Task objects from suggested_tasks.

        This converts the LLM-suggested tasks into real Task objects
        that the user can track and complete.
        """
        milestone = self.get_object()

        if not milestone.suggested_tasks:
            return Response(
                {
                    "success": False,
                    "error": "no_suggested_tasks",
                    "message": "No suggested tasks to create.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse suggested_tasks through DTO
        tasks_dtos = [TaskInputDTO.model_validate(t) for t in milestone.suggested_tasks]

        # Calculate milestone start date (previous milestone's end or goal start)
        goal = milestone.goal
        previous_milestone = (
            Milestone.objects.filter(goal=goal, order__lt=milestone.order)
            .order_by("-order")
            .first()
        )

        if previous_milestone and previous_milestone.target_date:
            milestone_start = previous_milestone.target_date + timedelta(days=1)
        else:
            milestone_start = goal.start_date or timezone.now().date()

        milestone_end = milestone.target_date or (milestone_start + timedelta(days=7))

        # Calculate due dates for tasks
        task_due_dates = calculate_task_due_dates(
            tasks=tasks_dtos,
            milestone_start=milestone_start,
            milestone_end=milestone_end,
        )

        created_tasks = []
        for task_idx, task_dto in enumerate(tasks_dtos):
            task_due_date = task_due_dates[task_idx] if task_idx < len(task_due_dates) else None

            # Convert date to datetime (model expects DateTimeField)
            task_due_datetime = (
                timezone.make_aware(datetime.combine(task_due_date, time(23, 59)))
                if task_due_date
                else None
            )

            task = Task.objects.create(
                user=request.user,
                goal=goal,  # Link to goal for CASCADE delete
                title=task_dto.title,
                description=task_dto.description,
                priority=task_dto.priority,
                is_recurring=task_dto.is_recurring,
                recurrence_period=task_dto.recurrence_period,
                recurrence_target_count=1 if task_dto.is_recurring else None,
                due_date=task_due_datetime,  # Set calculated due date as datetime
                status=Task.Status.TODO,
            )
            MilestoneTaskLink.objects.create(
                milestone=milestone,
                task=task,
            )
            created_tasks.append(
                {
                    "id": task.id,
                    "title": task.title,
                }
            )

        return Response(
            {
                "success": True,
                "message": f"Created {len(created_tasks)} tasks.",
                "tasks": created_tasks,
            }
        )
