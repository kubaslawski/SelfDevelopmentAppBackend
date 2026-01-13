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
- Break down large goals into weekly/bi-weekly milestones that build progressively
- Start from the absolute basics (buying materials, finding resources, setting up environment)
- End with a concrete achievement (exam, public performance, measurable outcome)
- Each milestone should be a logical progression from the previous one
- Set realistic timeframes based on the user's availability
- Consider potential obstacles and suggest mitigation strategies
- Make tasks specific, measurable and immediately actionable
- Tasks should be small enough to complete in 1-2 hours maximum
- Encourage but don't overwhelm

Key principles:
1. PROGRESSIVE: Each milestone builds on the previous one
2. GRANULAR: Weekly or bi-weekly milestones, not monthly
3. REALISTIC: Account for user's time constraints and starting point
4. COMPLETE: From preparation to final achievement
5. ACTIONABLE: Every task should be something the user can do TODAY

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

GOAL_PLAN_TEMPLATE = """Based on the following information, create a detailed, granular plan to achieve this goal.

## Goal
{goal_title}
{goal_description}

## User's Answers to Clarifying Questions
{answers}

## Target Date
{target_date}

## CRITICAL: Milestone Duration Rules

**EVERY milestone MUST be exactly 1 week (7 days) or less.**

Calculate the total weeks from today to target_date and create that many weekly milestones:
- 1 month goal = 4 weekly milestones
- 2 months = 8 weekly milestones
- 3 months = 12 weekly milestones
- 6 months = 24 weekly milestones
- 12 months = 52 weekly milestones

DO NOT create monthly milestones. Always break down into weeks.

## Progressive Learning Structure

Each week should have a SPECIFIC, MEASURABLE focus:

### Week 1: Foundation & Setup
- Research best learning methods/resources
- Purchase/acquire necessary materials
- Set up learning environment
- Find mentor/teacher/community if needed
- Create learning schedule

### Week 2-3: Absolute Basics
- Learn the most fundamental concepts
- Start with easiest exercises
- Build daily habit (even 15 min/day)
- Track progress from day 1

### Week 4-8: Building Blocks
- Progressively harder concepts
- Regular practice sessions
- First small achievements
- Identify weaknesses early

### Remaining weeks until 80%: Skill Development
- Each week focuses on ONE specific skill/topic
- Week N: "Master [specific topic]"
- Include practice, review, and application
- Mini-milestones and checkpoints

### Final 20% of time: Achievement Preparation
- Review all material
- Mock tests/practice runs
- Final polishing
- The actual achievement

## Task Requirements

Each weekly milestone should have 4-8 tasks:
- Daily practice task (recurring, 15-60 min)
- 2-3 learning tasks (new material)
- 1-2 review tasks (consolidation)
- 1 assessment task (end of week check)

Tasks should be completable in 30 minutes to 2 hours maximum.

## Response Format

Respond ONLY with valid JSON:
{{
    "icon": "material-community icon name that best represents the goal (snake_case, e.g., 'brain', 'dumbbell', 'rocket-outline')",
    "summary": "2-3 sentence overview of the complete journey",
    "milestones": [
        {{
            "title": "Week 1: [Specific Focus]",
            "description": "By end of this week, you will have: [concrete outcomes]",
            "target_date": "YYYY-MM-DD",
            "requirements": "Prerequisites for this week",
            "success_criteria": "Checklist of what 'done' looks like",
            "tasks": [
                {{
                    "title": "Specific task title",
                    "description": "Step-by-step instructions",
                    "estimated_duration": "30 minutes|1 hour|2 hours",
                    "priority": "high|medium|low",
                    "is_recurring": false,
                    "recurrence_period": null,
                    "category": "preparation|learning|practice|review|achievement"
                }}
            ]
        }}
    ],
    "tips": ["4-5 specific, actionable tips"],
    "potential_obstacles": ["Obstacle → Solution pairs"],
    "motivation": "Personalized encouragement",
    "final_achievement": "Concrete success definition"
}}

## Example: Learning German to B2 (6 months)

Week 1: Setup & Fundamentals
- Task: Download Duolingo + Anki
- Task: Order German textbook (Menschen A1)
- Task: Find online tutor on iTalki
- Task: Create study schedule (1hr/day)
- Task: Learn alphabet & pronunciation rules

Week 2: First Words & Phrases
- Task: Learn 100 most common words
- Task: Master greetings & introductions
- Task: Daily: Duolingo 15 min
- Task: Daily: Anki flashcards 15 min
- Task: Watch 1 German video for beginners

Week 3: Basic Grammar
- Task: Learn present tense conjugation
- Task: Master articles (der/die/das)
- Task: Practice 20 basic sentences
- Task: First conversation with tutor

... and so on for ALL 24 weeks!

REMEMBER:
- NEVER skip weeks or combine them
- Each week = 7 days maximum
- Be SPECIFIC about what to learn each week
- Include the EXACT resources/apps to use"""


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
        formatted_answers = "\n".join(f"- **{key}**: {value}" for key, value in answers.items())
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
