"""
Domain services for Goals.

Responsible for orchestrating LLM calls and mapping to/from entities/DTOs.
"""

import logging
from datetime import date, datetime
from typing import Any, List

from django.utils import timezone

from core.llm import (
    LLMError,
    RateLimitExceeded,
    gemini_client,
)
from core.llm.prompts import (
    FALLBACK_QUESTIONS,
    GENERATE_QUESTIONS_TEMPLATE,
    GOAL_PLAN_TEMPLATE,
    GOAL_PLANNER_SYSTEM,
    QUESTION_GENERATOR_SYSTEM,
)

from .domain.entities import (
    GeneratedMilestone,
    GeneratedPlan,
    GeneratedQuestion,
    GeneratedTask,
    QuestionAnswer,
)
from .models import Goal

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Question Generation
# -----------------------------------------------------------------------------


def generate_questions(
    goal: Goal, user_id: int
) -> tuple[List[GeneratedQuestion], bool]:
    """
    Generate contextual questions for a goal using Gemini.

    Returns:
        Tuple of (questions, is_fallback) where is_fallback=True means LLM failed.
    """
    goal_description = (
        f"{goal.title}. {goal.description}" if goal.description else goal.title
    )

    try:
        prompt = GENERATE_QUESTIONS_TEMPLATE.format(goal_description=goal_description)

        response = gemini_client.generate_json(
            prompt=prompt,
            user_id=user_id,
            system_prompt=QUESTION_GENERATOR_SYSTEM,
        )

        # Parse response
        raw_questions = response.get("questions", [])
        questions = [
            GeneratedQuestion(
                id=q.get("id", f"q{idx+1}"),
                question=q.get("question", ""),
                type=q.get("type", "text"),
                placeholder=q.get("placeholder", ""),
                options=q.get("options", []) if q.get("type") == "choice" else [],
            )
            for idx, q in enumerate(raw_questions)
        ]
        return questions, False

    except RateLimitExceeded:
        logger.warning("Rate limit for user %s, using fallback questions", user_id)
        return _fallback_questions(), True
    except LLMError as e:
        logger.error("LLM error generating questions for goal %s: %s", goal.id, e)
        return _fallback_questions(), True
    except Exception as e:
        logger.exception("Unexpected error generating questions: %s", e)
        return _fallback_questions(), True


def _fallback_questions() -> List[GeneratedQuestion]:
    """Convert fallback dicts to entities."""
    return [
        GeneratedQuestion(
            id=q.get("id", f"q{idx+1}"),
            question=q.get("question", ""),
            type=q.get("type", "text"),
            placeholder=q.get("placeholder", ""),
            options=q.get("options", []) if q.get("type") == "choice" else [],
        )
        for idx, q in enumerate(FALLBACK_QUESTIONS)
    ]


# -----------------------------------------------------------------------------
# Plan Generation
# -----------------------------------------------------------------------------


def generate_plan(
    goal: Goal, answers: List[QuestionAnswer], user_id: int
) -> GeneratedPlan:
    """
    Generate a plan (milestones + tasks) using Gemini.
    Returns a GeneratedPlan entity.
    """
    # Format answers for prompt
    answers_text = "\n".join(
        f"Q: {a.question}\nA: {a.answer}" for a in answers
    )

    prompt = GOAL_PLAN_TEMPLATE.format(
        goal_title=goal.title,
        goal_description=goal.description or "",
        answers=answers_text,
        target_date=goal.target_date.isoformat(),
    )

    response = gemini_client.generate_json(
        prompt=prompt,
        user_id=user_id,
        system_prompt=GOAL_PLANNER_SYSTEM,
    )

    # Parse milestones
    milestones = []
    for ms in response.get("milestones", []):
        tasks = [
            GeneratedTask(
                title=t.get("title", ""),
                description=t.get("description", ""),
                estimated_duration=t.get("estimated_duration", "1 hour"),
                priority=t.get("priority", "medium"),
                is_recurring=t.get("is_recurring", False),
                recurrence_period=t.get("recurrence_period"),
                category=t.get("category", "learning"),
            )
            for t in ms.get("tasks", [])
        ]

        target_date = _parse_date(ms.get("target_date"))

        milestones.append(
            GeneratedMilestone(
                title=ms.get("title", ""),
                description=ms.get("description", ""),
                target_date=target_date,
                requirements=ms.get("requirements", ""),
                success_criteria=ms.get("success_criteria", ""),
                tasks=tasks,
            )
        )

    return GeneratedPlan(
        summary=response.get("summary", ""),
        milestones=milestones,
        tips=response.get("tips", []),
        potential_obstacles=response.get("potential_obstacles", []),
        motivation=response.get("motivation", ""),
        final_achievement=response.get("final_achievement", ""),
        icon=response.get("icon", ""),
    )


def _parse_date(value: Any) -> date:
    """Parse a date from various formats."""
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            pass
    return date.today()


# -----------------------------------------------------------------------------
# Persistence helpers
# -----------------------------------------------------------------------------


def save_questions(goal: Goal, questions: List[GeneratedQuestion]) -> None:
    """Persist generated questions onto the Goal."""
    goal.planning_questions = [
        {
            "id": q.id,
            "question": q.question,
            "type": q.type,
            "placeholder": q.placeholder,
            "options": q.options,
        }
        for q in questions
    ]
    goal.save(update_fields=["planning_questions", "updated_at"])


def save_plan(goal: Goal, plan: GeneratedPlan) -> None:
    """Persist generated plan onto the Goal."""
    goal.llm_generated_plan = {
        "icon": plan.icon,
        "summary": plan.summary,
        "milestones": [
            {
                "title": m.title,
                "description": m.description,
                "target_date": m.target_date.isoformat(),
                "requirements": m.requirements,
                "success_criteria": m.success_criteria,
                "tasks": [
                    {
                        "title": t.title,
                        "description": t.description,
                        "estimated_duration": t.estimated_duration,
                        "priority": t.priority,
                        "is_recurring": t.is_recurring,
                        "recurrence_period": t.recurrence_period,
                        "category": t.category,
                    }
                    for t in m.tasks
                ],
            }
            for m in plan.milestones
        ],
        "tips": plan.tips,
        "potential_obstacles": plan.potential_obstacles,
        "motivation": plan.motivation,
        "final_achievement": plan.final_achievement,
    }
    if not goal.icon and plan.icon:
        goal.icon = plan.icon
    goal.plan_generated_at = timezone.now()
    goal.motivation = plan.motivation
    goal.potential_obstacles = plan.potential_obstacles
    goal.tips = plan.tips
    goal.final_achievement = plan.final_achievement
    goal.status = Goal.Status.DRAFT
    goal.save()
