"""
Services for computing and updating statistics.
"""

from collections import defaultdict
from datetime import timedelta
from typing import Optional

from django.db.models import Count, Sum
from django.utils import timezone

from apps.goals.models import Goal, Milestone
from apps.tasks.models import Task, TaskCompletion

from .models import (
    DailyProductivity,
    GoalProgress,
    GroupRanking,
    HabitPerformance,
    PeriodComparison,
    PersonalRecord,
    UserStreak,
)


# =============================================================================
# User Streak Services
# =============================================================================


def get_or_create_streak(user) -> UserStreak:
    """Get or create streak record for user."""
    streak, _ = UserStreak.objects.get_or_create(user=user)
    return streak


def update_user_streak(user, activity_date=None):
    """
    Update user's streak after task completion.

    Called when a task is completed.
    """
    streak = get_or_create_streak(user)
    streak.update_streak(activity_date)
    return streak


def check_all_streaks():
    """
    Check all streaks for broken status.

    Should be run daily via Celery task.
    """
    for streak in UserStreak.objects.filter(current_streak__gt=0):
        streak.check_streak_broken()


def recalculate_user_streak(user) -> UserStreak:
    """
    Recalculate streak from scratch based on TaskCompletion data.

    Useful for fixing inconsistencies.
    """
    streak = get_or_create_streak(user)

    # Get all completion dates for this user
    completion_dates = set(
        TaskCompletion.objects.filter(task__user=user)
        .values_list("completed_at__date", flat=True)
        .distinct()
    )

    # Add non-recurring completed tasks
    non_recurring_dates = set(
        Task.objects.filter(
            user=user,
            status=Task.Status.COMPLETED,
            completed_at__isnull=False
        ).values_list("completed_at__date", flat=True)
    )

    all_dates = sorted(completion_dates | non_recurring_dates)

    if not all_dates:
        streak.current_streak = 0
        streak.longest_streak = 0
        streak.current_streak_start = None
        streak.last_activity_date = None
        streak.save()
        return streak

    # Calculate streaks
    current_streak = 1
    longest_streak = 1
    streak_start = all_dates[0]
    longest_start = all_dates[0]
    longest_end = all_dates[0]

    for i in range(1, len(all_dates)):
        diff = (all_dates[i] - all_dates[i-1]).days
        if diff == 1:
            current_streak += 1
        elif diff > 1:
            if current_streak > longest_streak:
                longest_streak = current_streak
                longest_start = streak_start
                longest_end = all_dates[i-1]
            current_streak = 1
            streak_start = all_dates[i]

    # Check final streak
    if current_streak > longest_streak:
        longest_streak = current_streak
        longest_start = streak_start
        longest_end = all_dates[-1]

    # Check if current streak is still active
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    last_date = all_dates[-1]

    if last_date < yesterday:
        # Streak is broken
        if current_streak >= longest_streak:
            longest_streak = current_streak
            longest_start = streak_start
            longest_end = last_date
        current_streak = 0
        streak_start = None

    streak.current_streak = current_streak
    streak.current_streak_start = streak_start
    streak.last_activity_date = last_date
    streak.longest_streak = longest_streak
    streak.longest_streak_start = longest_start
    streak.longest_streak_end = longest_end
    streak.save()

    return streak


# =============================================================================
# Daily Productivity Services
# =============================================================================


def get_or_create_daily_productivity(user, date) -> DailyProductivity:
    """Get or create daily productivity record."""
    record, _ = DailyProductivity.objects.get_or_create(
        user=user,
        date=date,
    )
    return record


def update_daily_productivity(user, date=None):
    """
    Update daily productivity stats for a specific date.
    """
    if date is None:
        date = timezone.now().date()

    record = get_or_create_daily_productivity(user, date)

    # Get completions for this day
    day_start = timezone.make_aware(
        timezone.datetime.combine(date, timezone.datetime.min.time())
    )
    day_end = day_start + timedelta(days=1)

    # Task completions (recurring)
    completions = TaskCompletion.objects.filter(
        task__user=user,
        completed_at__gte=day_start,
        completed_at__lt=day_end,
    )

    record.habit_completions = completions.count()

    # Time spent
    time_sum = completions.aggregate(total=Sum("completed_value"))["total"] or 0
    record.total_time_spent = int(time_sum)

    # Completions by hour
    hour_counts = defaultdict(int)
    for c in completions:
        hour = c.completed_at.hour
        hour_counts[str(hour)] = hour_counts.get(str(hour), 0) + 1

    # Non-recurring tasks completed
    non_recurring = Task.objects.filter(
        user=user,
        is_recurring=False,
        status=Task.Status.COMPLETED,
        completed_at__gte=day_start,
        completed_at__lt=day_end,
    )

    for t in non_recurring:
        hour = t.completed_at.hour
        hour_counts[str(hour)] = hour_counts.get(str(hour), 0) + 1

    record.tasks_completed = record.habit_completions + non_recurring.count()
    record.completions_by_hour = dict(hour_counts)

    # Tasks created
    record.tasks_created = Task.objects.filter(
        user=user,
        created_at__gte=day_start,
        created_at__lt=day_end,
    ).count()

    # Milestones completed
    record.milestones_completed = Milestone.objects.filter(
        goal__user=user,
        status=Milestone.Status.COMPLETED,
        completed_at__gte=day_start,
        completed_at__lt=day_end,
    ).count()

    record.save()
    return record


def get_productivity_summary(user, start_date, end_date) -> dict:
    """
    Get productivity summary for a date range.
    """
    records = DailyProductivity.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date,
    ).order_by("date")

    # Aggregate totals
    totals = records.aggregate(
        total_tasks=Sum("tasks_completed"),
        total_habits=Sum("habit_completions"),
        total_time=Sum("total_time_spent"),
    )

    total_tasks = totals["total_tasks"] or 0
    total_habits = totals["total_habits"] or 0
    total_time = totals["total_time"] or 0

    # Calculate days in range
    days = (end_date - start_date).days + 1
    avg_tasks = total_tasks / days if days > 0 else 0

    # Find peak hour
    hour_totals = defaultdict(int)
    for r in records:
        for hour, count in r.completions_by_hour.items():
            hour_totals[int(hour)] += count

    peak_hour = None
    peak_count = 0
    if hour_totals:
        peak_hour = max(hour_totals, key=hour_totals.get)
        peak_count = hour_totals[peak_hour]

    # Find best day
    best_day = None
    best_count = 0
    for r in records:
        if r.tasks_completed > best_count:
            best_count = r.tasks_completed
            best_day = r.date

    return {
        "period_start": start_date,
        "period_end": end_date,
        "total_tasks_completed": total_tasks,
        "total_habit_completions": total_habits,
        "total_time_spent": total_time,
        "average_tasks_per_day": round(avg_tasks, 1),
        "peak_hour": peak_hour,
        "peak_hour_count": peak_count,
        "best_day": best_day,
        "best_day_count": best_count,
        "daily_breakdown": list(records),
    }


# =============================================================================
# Habit Performance Services
# =============================================================================


def get_or_create_habit_performance(task) -> Optional[HabitPerformance]:
    """Get or create habit performance for a recurring task."""
    if not task.is_recurring:
        return None

    perf, _ = HabitPerformance.objects.get_or_create(task=task)
    return perf


def update_habit_performance(task):
    """
    Update performance metrics for a recurring task.
    """
    if not task.is_recurring:
        return None

    perf = get_or_create_habit_performance(task)
    today = timezone.now().date()

    # Get all completions
    completions = task.completions.all()
    perf.total_completions = completions.count()

    # Last 7 days
    week_ago = today - timedelta(days=7)
    perf.completions_last_7_days = completions.filter(
        completed_at__date__gte=week_ago
    ).count()

    # Last 30 days
    month_ago = today - timedelta(days=30)
    perf.completions_last_30_days = completions.filter(
        completed_at__date__gte=month_ago
    ).count()

    # Last completion
    last = completions.order_by("-completed_at").first()
    perf.last_completion_date = last.completed_at.date() if last else None

    # Calculate consistency (% of periods with at least one completion)
    # For daily tasks: % of days with completion in last 30 days
    # For weekly: % of weeks, etc.
    target = task.recurrence_target_count or 1

    if task.recurrence_period == Task.RecurrencePeriod.DAILY:
        expected = 30  # 30 days
        days_with_completion = completions.filter(
            completed_at__date__gte=month_ago
        ).values("completed_at__date").distinct().count()
        perf.consistency_rate = min(100, (days_with_completion / expected) * 100)
    else:
        # Simplified: just use last 30 days completion rate
        perf.consistency_rate = min(100, (perf.completions_last_30_days / 30) * 100)

    # Determine trend
    first_half = completions.filter(
        completed_at__date__gte=month_ago,
        completed_at__date__lt=today - timedelta(days=15),
    ).count()
    second_half = completions.filter(
        completed_at__date__gte=today - timedelta(days=15),
    ).count()

    if second_half > first_half * 1.2:
        perf.trend = "improving"
    elif second_half < first_half * 0.5:
        perf.trend = "at_risk"
    elif second_half < first_half * 0.8:
        perf.trend = "declining"
    else:
        perf.trend = "stable"

    # Build heatmap (last 365 days)
    year_ago = today - timedelta(days=365)
    heatmap_data = {}
    for c in completions.filter(completed_at__date__gte=year_ago):
        date_str = c.completed_at.date().isoformat()
        heatmap_data[date_str] = heatmap_data.get(date_str, 0) + 1
    perf.completion_heatmap = heatmap_data

    # Calculate streak
    dates = sorted(set(
        c.completed_at.date() for c in completions
    ), reverse=True)

    streak = 0
    if dates and dates[0] >= today - timedelta(days=1):
        streak = 1
        for i in range(1, len(dates)):
            if (dates[i-1] - dates[i]).days == 1:
                streak += 1
            else:
                break

    perf.current_streak = streak
    if streak > perf.longest_streak:
        perf.longest_streak = streak

    perf.save()
    return perf


def get_habits_summary(user) -> dict:
    """Get summary of all habits for a user - only active recurring tasks."""
    habits = HabitPerformance.objects.filter(
        task__user=user,
        task__is_recurring=True,
        task__is_active=True,
    ).select_related("task")

    total = habits.count()
    avg_consistency = 0
    if total > 0:
        avg_consistency = sum(h.consistency_rate for h in habits) / total

    return {
        "total_habits": total,
        "average_consistency": round(avg_consistency, 1),
        "best_habits": list(habits.filter(consistency_rate__gte=80).order_by("-consistency_rate")[:5]),
        "at_risk_habits": list(habits.filter(trend="at_risk")),
        "improving_habits": list(habits.filter(trend="improving")),
    }


# =============================================================================
# Goal Progress Services
# =============================================================================


def get_or_create_goal_progress(goal) -> GoalProgress:
    """Get or create goal progress record."""
    progress, _ = GoalProgress.objects.get_or_create(goal=goal)
    return progress


def update_goal_progress(goal):
    """Update progress stats for a goal."""
    progress = get_or_create_goal_progress(goal)
    today = timezone.now().date()

    # Milestones
    milestones = goal.milestones.all()
    progress.milestones_total = milestones.count()
    progress.milestones_completed = milestones.filter(
        status=Milestone.Status.COMPLETED
    ).count()

    # Progress percentage
    if progress.milestones_total > 0:
        progress.progress_percentage = (
            progress.milestones_completed / progress.milestones_total
        ) * 100
    else:
        progress.progress_percentage = 0

    # Tasks linked to goal
    from apps.goals.models import MilestoneTaskLink
    task_links = MilestoneTaskLink.objects.filter(
        milestone__goal=goal
    ).select_related("task")

    progress.tasks_total = task_links.count()
    progress.tasks_completed = task_links.filter(
        task__status=Task.Status.COMPLETED
    ).count()

    # Velocity calculation
    if goal.start_date and goal.target_date:
        total_days = (goal.target_date - goal.start_date).days
        days_elapsed = (today - goal.start_date).days

        if days_elapsed > 0 and total_days > 0:
            progress.velocity = progress.progress_percentage / days_elapsed

            # Estimated completion
            if progress.velocity > 0:
                remaining = 100 - progress.progress_percentage
                days_needed = remaining / progress.velocity
                progress.estimated_completion_date = today + timedelta(days=int(days_needed))

            # Days ahead/behind
            expected_progress = (days_elapsed / total_days) * 100
            diff = progress.progress_percentage - expected_progress
            progress.days_ahead_or_behind = int(diff * total_days / 100)
            progress.on_track = diff >= -10  # 10% tolerance

    # Velocity trend (compare last 2 weeks)
    # Simplified: based on recent activity
    recent_completions = milestones.filter(
        status=Milestone.Status.COMPLETED,
        completed_at__gte=timezone.now() - timedelta(days=14),
    ).count()

    if recent_completions > 0:
        progress.velocity_trend = "steady"
    elif progress.days_since_activity > 7:
        progress.velocity_trend = "stalled"
    else:
        progress.velocity_trend = "steady"

    # Last activity
    last_milestone = milestones.filter(
        completed_at__isnull=False
    ).order_by("-completed_at").first()

    if last_milestone:
        progress.last_activity_date = last_milestone.completed_at.date()
        progress.days_since_activity = (today - progress.last_activity_date).days

    progress.save()
    return progress


def get_goals_summary(user) -> dict:
    """Get summary of all goals for a user."""
    goals = GoalProgress.objects.filter(
        goal__user=user,
        goal__status__in=[Goal.Status.ACTIVE, Goal.Status.PLANNING],
    ).select_related("goal")

    total = goals.count()
    active = goals.filter(goal__status=Goal.Status.ACTIVE).count()
    on_track = goals.filter(on_track=True).count()
    behind = goals.filter(on_track=False).count()

    avg_progress = 0
    if total > 0:
        avg_progress = sum(g.progress_percentage for g in goals) / total

    return {
        "total_goals": total,
        "active_goals": active,
        "on_track_count": on_track,
        "behind_count": behind,
        "average_progress": round(avg_progress, 1),
        "goals": list(goals),
    }


# =============================================================================
# Personal Records Services
# =============================================================================


def check_and_update_records(user, record_type: str, value: int, context: dict = None):
    """
    Check if a value beats the current record and update if so.
    """
    today = timezone.now().date()

    # Get current record
    current = PersonalRecord.objects.filter(
        user=user,
        record_type=record_type,
        is_current=True,
    ).first()

    if current and current.value >= value:
        return None  # Not a new record

    # Mark old record as not current
    if current:
        current.is_current = False
        current.save()

    # Create new record
    new_record = PersonalRecord.objects.create(
        user=user,
        record_type=record_type,
        value=value,
        achieved_date=today,
        context=context or {},
        is_current=True,
    )

    return new_record


def get_user_records(user) -> dict:
    """Get all current personal records for a user."""
    records = PersonalRecord.objects.filter(
        user=user,
        is_current=True,
    ).order_by("record_type")

    recent = PersonalRecord.objects.filter(
        user=user,
    ).order_by("-achieved_at")[:10]

    return {
        "records": list(records),
        "recent_records": list(recent),
    }


# =============================================================================
# Period Comparison Services
# =============================================================================


def get_week_bounds(date):
    """Get start and end of week containing date (Monday-Sunday)."""
    start = date - timedelta(days=date.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_month_bounds(date):
    """Get start and end of month containing date."""
    start = date.replace(day=1)
    if date.month == 12:
        end = date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
    return start, end


def get_or_create_period_comparison(user, period_type: str, period_start) -> PeriodComparison:
    """Get or create period comparison record."""
    if period_type == PeriodComparison.PeriodType.WEEK:
        start, end = get_week_bounds(period_start)
    else:
        start, end = get_month_bounds(period_start)

    record, _ = PeriodComparison.objects.get_or_create(
        user=user,
        period_type=period_type,
        period_start=start,
        defaults={"period_end": end},
    )
    return record


def update_period_comparison(user, period_type: str, period_start):
    """Update period comparison stats."""
    record = get_or_create_period_comparison(user, period_type, period_start)

    # Get daily stats for this period
    daily_stats = DailyProductivity.objects.filter(
        user=user,
        date__gte=record.period_start,
        date__lte=record.period_end,
    )

    totals = daily_stats.aggregate(
        tasks=Sum("tasks_completed"),
        created=Sum("tasks_created"),
        habits=Sum("habit_completions"),
        time=Sum("total_time_spent"),
        milestones=Sum("milestones_completed"),
    )

    record.tasks_completed = totals["tasks"] or 0
    record.tasks_created = totals["created"] or 0
    record.habit_completions = totals["habits"] or 0
    record.time_spent_minutes = totals["time"] or 0
    record.milestones_completed = totals["milestones"] or 0

    # Calculate productivity score (0-100)
    # Simple formula: tasks * 10 + habits * 5 + milestones * 20, capped at 100
    score = min(100, record.tasks_completed * 10 + record.habit_completions * 5 + record.milestones_completed * 20)
    record.productivity_score = score

    # Get previous period for comparison
    if period_type == PeriodComparison.PeriodType.WEEK:
        prev_start = record.period_start - timedelta(days=7)
    else:
        prev_start = record.period_start - timedelta(days=30)

    prev_record = PeriodComparison.objects.filter(
        user=user,
        period_type=period_type,
        period_start=prev_start,
    ).first()

    if prev_record and prev_record.tasks_completed > 0:
        change = record.tasks_completed - prev_record.tasks_completed
        record.tasks_change_percent = (change / prev_record.tasks_completed) * 100

    record.save()
    return record


def compare_periods(user, period_type: str) -> dict:
    """Compare current period with previous period."""
    today = timezone.now().date()

    if period_type == PeriodComparison.PeriodType.WEEK:
        current_start, _ = get_week_bounds(today)
        prev_start = current_start - timedelta(days=7)
    else:
        current_start, _ = get_month_bounds(today)
        prev_start = current_start - timedelta(days=30)

    current = update_period_comparison(user, period_type, current_start)
    prev = PeriodComparison.objects.filter(
        user=user,
        period_type=period_type,
        period_start__lte=prev_start,
    ).order_by("-period_start").first()

    # Calculate changes
    tasks_change = current.tasks_completed - (prev.tasks_completed if prev else 0)
    tasks_pct = (tasks_change / prev.tasks_completed * 100) if prev and prev.tasks_completed else 0

    habits_change = current.habit_completions - (prev.habit_completions if prev else 0)
    habits_pct = (habits_change / prev.habit_completions * 100) if prev and prev.habit_completions else 0

    time_change = current.time_spent_minutes - (prev.time_spent_minutes if prev else 0)
    time_pct = (time_change / prev.time_spent_minutes * 100) if prev and prev.time_spent_minutes else 0

    is_improvement = tasks_change >= 0 and habits_change >= 0

    if is_improvement:
        summary = f"Great job! You completed {tasks_change} more tasks than last {period_type}."
    else:
        summary = f"You completed {abs(tasks_change)} fewer tasks than last {period_type}. Keep going!"

    return {
        "current_period": current,
        "previous_period": prev,
        "tasks_change": tasks_change,
        "tasks_change_percent": round(tasks_pct, 1),
        "habits_change": habits_change,
        "habits_change_percent": round(habits_pct, 1),
        "time_change": time_change,
        "time_change_percent": round(time_pct, 1),
        "is_improvement": is_improvement,
        "summary": summary,
    }

