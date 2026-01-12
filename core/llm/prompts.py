"""
Prompt templates for LLM interactions.

All prompts should be defined here for easy management and versioning.
"""

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

GOAL_PLANNER_SYSTEM = """You are an expert life coach and goal planning assistant.
Your role is to help users create actionable, realistic plans to achieve their goals.

When creating plans:
- Break down large goals into smaller, manageable milestones
- Set realistic timeframes based on the user's availability
- Consider potential obstacles and suggest mitigation strategies
- Make tasks specific and measurable
- Encourage but don't overwhelm

Always respond in the same language the user uses."""


QUESTION_GENERATOR_SYSTEM = """You are a helpful assistant that asks clarifying questions.
Your role is to understand the user's goal better by asking relevant, specific questions.

Rules:
- Ask 3-5 questions maximum
- Questions should be specific to the goal, not generic
- Questions should help understand: current situation, resources, time, constraints
- Be friendly and encouraging
- Ask in the same language the user uses"""


# =============================================================================
# QUESTION GENERATION (Step 1: Generate contextual questions)
# =============================================================================

GENERATE_QUESTIONS_TEMPLATE = """The user wants to achieve this goal:

"{goal_description}"

Generate 3-5 specific clarifying questions that will help create a personalized plan.

Questions should cover:
1. Current situation/experience level
2. Available resources (time, money, equipment, etc.)
3. Specific preferences or constraints
4. Timeline expectations

Respond ONLY with valid JSON in this format:
{{
    "questions": [
        {{
            "id": "q1",
            "question": "The question text",
            "type": "text|choice|number",
            "placeholder": "Example answer or hint",
            "options": ["Option 1", "Option 2"]  // only for type "choice"
        }}
    ]
}}

Make questions specific to: "{goal_description}"
Do NOT ask generic questions. Tailor each question to this specific goal."""


# =============================================================================
# PLAN GENERATION (Step 2: Generate plan based on answers)
# =============================================================================

GOAL_PLAN_TEMPLATE = """Based on the following information, create a detailed plan to achieve this goal.

## Goal
{goal_title}
{goal_description}

## User's Answers to Clarifying Questions
{answers}

## Target Date
{target_date}

## Instructions
Create a structured plan with:
1. **Milestones**: Key checkpoints on the way to the goal (3-5 milestones)
2. **Tasks**: Specific actions for each milestone (2-4 tasks per milestone)
3. **Timeline**: Suggested dates for each milestone (spread evenly until target date)
4. **Tips**: Practical advice for staying on track

Important:
- Make milestones achievable and measurable
- Tasks should be specific actions, not vague goals
- Consider the user's available time and resources from their answers
- Be encouraging but realistic

Respond ONLY with valid JSON in the following format:
{{
    "summary": "Brief summary of the plan approach (2-3 sentences)",
    "milestones": [
        {{
            "title": "Milestone title",
            "description": "What achieving this milestone means",
            "target_date": "YYYY-MM-DD",
            "tasks": [
                {{
                    "title": "Specific task title",
                    "description": "What to do and how",
                    "estimated_duration": "e.g., 30 minutes, 2 hours",
                    "priority": "high|medium|low",
                    "is_recurring": false,
                    "recurrence_period": null
                }}
            ]
        }}
    ],
    "tips": ["Practical tip 1", "Practical tip 2", "Practical tip 3"],
    "potential_obstacles": ["Obstacle 1 and how to overcome it", "Obstacle 2 and solution"],
    "motivation": "An encouraging, personalized message for the user based on their goal"
}}"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_generate_questions_prompt(goal_description: str) -> str:
    """
    Format the prompt for generating contextual questions.

    Args:
        goal_description: What the user wants to achieve.

    Returns:
        Formatted prompt string.
    """
    return GENERATE_QUESTIONS_TEMPLATE.format(
        goal_description=goal_description,
    )


def format_goal_plan_prompt(
    goal_title: str,
    goal_description: str,
    answers: dict | list,
    target_date: str,
) -> str:
    """
    Format the goal planning prompt with user's data.

    Args:
        goal_title: The title of the goal.
        goal_description: Detailed description of the goal.
        answers: Dictionary or list of user's answers to questions.
        target_date: Target completion date (YYYY-MM-DD format).

    Returns:
        Formatted prompt string.
    """
    # Format answers as readable text
    if isinstance(answers, dict):
        formatted_answers = "\n".join(
            f"- **{key}**: {value}" for key, value in answers.items()
        )
    elif isinstance(answers, list):
        # List of {question, answer} objects
        formatted_answers = "\n".join(
            f"- **Q**: {item.get('question', 'Question')}\n  **A**: {item.get('answer', 'No answer')}"
            for item in answers
        )
    else:
        formatted_answers = str(answers)

    return GOAL_PLAN_TEMPLATE.format(
        goal_title=goal_title,
        goal_description=goal_description or "No additional description provided.",
        answers=formatted_answers,
        target_date=target_date,
    )


# =============================================================================
# LEGACY (kept for backwards compatibility)
# =============================================================================

# Static questions - can be used as fallback if LLM fails
FALLBACK_QUESTIONS = [
    {
        "id": "experience",
        "question": "What's your current experience or starting point?",
        "type": "text",
        "placeholder": "e.g., Complete beginner, some experience, etc.",
    },
    {
        "id": "time_available",
        "question": "How much time can you dedicate to this goal weekly?",
        "type": "text",
        "placeholder": "e.g., 5 hours per week",
    },
    {
        "id": "resources",
        "question": "What resources do you already have?",
        "type": "text",
        "placeholder": "e.g., Equipment, budget, support from others",
    },
    {
        "id": "obstacles",
        "question": "What challenges do you anticipate?",
        "type": "text",
        "placeholder": "e.g., Busy schedule, limited budget",
    },
    {
        "id": "motivation",
        "question": "Why is this goal important to you?",
        "type": "text",
        "placeholder": "What drives you to achieve this?",
    },
]
