"""
Views for Goals API.

Flow for creating a goal with AI-generated plan:
1. POST /goals/ - Create goal with title, description, target_date
2. POST /goals/{id}/generate_questions/ - LLM generates contextual questions
3. POST /goals/{id}/submit_answers/ - User submits answers, LLM generates plan
4. POST /goals/{id}/apply_plan/ - Create Milestone objects from plan
"""

import logging

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .domain.entities import QuestionAnswer
from .models import Goal, Milestone
from .serializers import (
    GoalListSerializer,
    GoalDetailSerializer,
    GoalCreateSerializer,
    SubmitAnswersSerializer,
    MilestoneSerializer,
)
from .services import (
    generate_questions,
    generate_plan,
    save_questions,
    save_plan,
)

logger = logging.getLogger(__name__)


class GoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Goals.

    Provides CRUD operations plus custom actions for:
    - Generating contextual questions (LLM)
    - Submitting answers and generating plan (LLM)
    - Applying generated plan (creating milestones)
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter goals to current user only."""
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

        # Don't regenerate if already has questions and user didn't force
        if goal.planning_questions and not request.data.get("force", False):
            return Response({
                "success": True,
                "questions": goal.planning_questions,
                "cached": True,
            })

        questions = generate_questions(goal=goal, user_id=request.user.id)
        save_questions(goal, questions)

        return Response({
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
        })

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

            plan = generate_plan(goal=goal, answers=answer_entities, user_id=request.user.id)
            save_plan(goal, plan)

            return Response({
                "success": True,
                "plan": goal.llm_generated_plan,
                "message": "Plan generated successfully. Review and apply when ready.",
            })

        except RateLimitExceeded as e:
            goal.status = Goal.Status.DRAFT
            goal.save(update_fields=["status", "updated_at"])
            return Response({
                "success": False,
                "error": "rate_limit_exceeded",
                "message": str(e),
                "retry_after": e.retry_after,
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        except Exception as e:
            logger.error("Error generating plan for goal %s: %s", goal.id, e)
            goal.status = Goal.Status.DRAFT
            goal.save(update_fields=["status", "updated_at"])
            return Response({
                "success": False,
                "error": "llm_error",
                "message": "Failed to generate plan. Please try again later.",
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

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
            return Response({
                "success": False,
                "error": "no_plan",
                "message": "No plan has been generated yet. Generate a plan first.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Use provided milestones or fall back to LLM-generated ones
        milestones_data = request.data.get("milestones") or goal.llm_generated_plan.get("milestones", [])

        if not milestones_data:
            return Response({
                "success": False,
                "error": "no_milestones",
                "message": "No milestones in the plan.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Delete existing milestones if any
        goal.milestones.all().delete()

        # Create milestones from plan
        created_milestones = []
        for idx, milestone_data in enumerate(milestones_data):
            milestone = Milestone.objects.create(
                goal=goal,
                title=milestone_data.get("title", f"Milestone {idx + 1}"),
                description=milestone_data.get("description", ""),
                order=idx,
                target_date=milestone_data.get("target_date"),
                suggested_tasks=milestone_data.get("tasks", []),
                status=Milestone.Status.PENDING,
            )
            created_milestones.append(milestone)

        # Activate the goal
        goal.status = Goal.Status.ACTIVE
        if not goal.start_date:
            goal.start_date = timezone.now().date()
        goal.save(update_fields=["status", "start_date", "updated_at"])

        return Response({
            "success": True,
            "message": f"Plan applied with {len(created_milestones)} milestones.",
            "goal": GoalDetailSerializer(goal).data,
        })

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

        return Response({
            "success": True,
            "message": "Congratulations! Goal marked as completed.",
            "goal": GoalDetailSerializer(goal).data,
        })

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause the goal."""
        goal = self.get_object()
        goal.status = Goal.Status.PAUSED
        goal.save(update_fields=["status", "updated_at"])

        return Response({
            "success": True,
            "goal": GoalDetailSerializer(goal).data,
        })

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """Resume a paused goal."""
        goal = self.get_object()
        goal.status = Goal.Status.ACTIVE
        goal.save(update_fields=["status", "updated_at"])

        return Response({
            "success": True,
            "goal": GoalDetailSerializer(goal).data,
        })

    @action(detail=True, methods=["post"])
    def abandon(self, request, pk=None):
        """Abandon the goal."""
        goal = self.get_object()
        goal.status = Goal.Status.ABANDONED
        goal.save(update_fields=["status", "updated_at"])

        return Response({
            "success": True,
            "goal": GoalDetailSerializer(goal).data,
        })


class MilestoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Milestones.

    Milestones are always accessed in context of a Goal.
    """

    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter milestones to current user's goals only."""
        return Milestone.objects.filter(
            goal__user=self.request.user
        ).select_related("goal")

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark the milestone as completed."""
        milestone = self.get_object()
        milestone.mark_completed()

        return Response({
            "success": True,
            "milestone": MilestoneSerializer(milestone).data,
        })

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """Start working on the milestone."""
        milestone = self.get_object()
        milestone.status = Milestone.Status.IN_PROGRESS
        milestone.save(update_fields=["status", "updated_at"])

        return Response({
            "success": True,
            "milestone": MilestoneSerializer(milestone).data,
        })

    @action(detail=True, methods=["post"])
    def skip(self, request, pk=None):
        """Skip this milestone."""
        milestone = self.get_object()
        milestone.status = Milestone.Status.SKIPPED
        milestone.save(update_fields=["status", "updated_at"])

        return Response({
            "success": True,
            "milestone": MilestoneSerializer(milestone).data,
        })

    @action(detail=True, methods=["post"])
    def create_tasks(self, request, pk=None):
        """
        Create actual Task objects from suggested_tasks.

        This converts the LLM-suggested tasks into real Task objects
        that the user can track and complete.
        """
        from apps.tasks.models import Task
        from .models import MilestoneTaskLink

        milestone = self.get_object()

        if not milestone.suggested_tasks:
            return Response({
                "success": False,
                "error": "no_suggested_tasks",
                "message": "No suggested tasks to create.",
            }, status=status.HTTP_400_BAD_REQUEST)

        created_tasks = []
        for task_data in milestone.suggested_tasks:
            task = Task.objects.create(
                user=request.user,
                title=task_data.get("title", "Task"),
                description=task_data.get("description", ""),
                priority=task_data.get("priority", "medium"),
                status=Task.Status.TODO,
            )
            MilestoneTaskLink.objects.create(
                milestone=milestone,
                task=task,
            )
            created_tasks.append({
                "id": task.id,
                "title": task.title,
            })

        return Response({
            "success": True,
            "message": f"Created {len(created_tasks)} tasks.",
            "tasks": created_tasks,
        })
