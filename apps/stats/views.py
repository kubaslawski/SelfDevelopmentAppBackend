"""
Views for Stats app.
"""

from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    DailyProductivity,
    GoalProgress,
    HabitPerformance,
    PeriodComparison,
    PersonalRecord,
)
from .serializers import (
    ComparisonResultSerializer,
    DailyProductivitySerializer,
    DashboardStatsSerializer,
    GoalProgressSerializer,
    GoalsSummarySerializer,
    GroupLeaderboardSerializer,
    HabitPerformanceSerializer,
    HabitSummarySerializer,
    PeriodComparisonSerializer,
    PersonalRecordSerializer,
    PersonalRecordsSummarySerializer,
    ProductivitySummarySerializer,
    UserStreakSerializer,
)
from .services import (
    compare_periods,
    get_goals_summary,
    get_habits_summary,
    get_or_create_streak,
    get_productivity_summary,
    get_user_records,
    recalculate_user_streak,
    update_daily_productivity,
)


# =============================================================================
# User Streak
# =============================================================================


class UserStreakView(APIView):
    """
    Get current user's streak information.
    
    GET: Get streak data (current streak, longest streak, etc.)
    POST: Recalculate streak from task history (fixes inconsistencies)
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_streak_get",
        summary="Get user streak",
        responses={200: UserStreakSerializer},
    )
    def get(self, request):
        """Get current user's streak."""
        streak = get_or_create_streak(request.user)
        streak.check_streak_broken()  # Update if broken
        serializer = UserStreakSerializer(streak)
        return Response(serializer.data)

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_streak_recalculate",
        summary="Recalculate streak",
        description="Recalculate streak from task completion history. Use if streak seems incorrect.",
        request=None,
        responses={200: UserStreakSerializer},
    )
    def post(self, request):
        """Recalculate streak from history."""
        streak = recalculate_user_streak(request.user)
        serializer = UserStreakSerializer(streak)
        return Response(serializer.data)


# =============================================================================
# Daily Productivity
# =============================================================================


class DailyProductivityView(APIView):
    """
    Get productivity stats for a specific day or date range.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_productivity_get",
        summary="Get daily productivity",
        parameters=[
            OpenApiParameter(
                name="date",
                description="Specific date (YYYY-MM-DD). Defaults to today.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="start_date",
                description="Start date for range (YYYY-MM-DD)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="end_date",
                description="End date for range (YYYY-MM-DD)",
                required=False,
                type=str,
            ),
        ],
        responses={200: ProductivitySummarySerializer},
    )
    def get(self, request):
        """Get daily productivity stats."""
        today = timezone.now().date()
        
        # Single day
        date_str = request.query_params.get("date")
        if date_str:
            try:
                date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Update stats for this day
            record = update_daily_productivity(request.user, date)
            serializer = DailyProductivitySerializer(record)
            return Response(serializer.data)
        
        # Date range
        start_str = request.query_params.get("start_date")
        end_str = request.query_params.get("end_date")
        
        if start_str and end_str:
            try:
                start_date = timezone.datetime.strptime(start_str, "%Y-%m-%d").date()
                end_date = timezone.datetime.strptime(end_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Default: last 7 days
            end_date = today
            start_date = today - timedelta(days=6)
        
        # Update stats for each day in range
        current = start_date
        while current <= end_date:
            update_daily_productivity(request.user, current)
            current += timedelta(days=1)
        
        summary = get_productivity_summary(request.user, start_date, end_date)
        serializer = ProductivitySummarySerializer(summary)
        return Response(serializer.data)


class TodayStatsView(APIView):
    """Quick endpoint for today's stats."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_today_get",
        summary="Get today's stats",
        responses={200: DailyProductivitySerializer},
    )
    def get(self, request):
        """Get today's productivity stats."""
        today = timezone.now().date()
        record = update_daily_productivity(request.user, today)
        serializer = DailyProductivitySerializer(record)
        return Response(serializer.data)


# =============================================================================
# Habit Performance
# =============================================================================


class HabitPerformanceView(APIView):
    """
    Get performance stats for recurring tasks (habits).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_habits_list",
        summary="Get habits performance",
        responses={200: HabitSummarySerializer},
    )
    def get(self, request):
        """Get summary of all habits."""
        from .services import update_habit_performance
        from apps.tasks.models import Task
        
        # Update all habit performances
        habits = Task.objects.filter(user=request.user, is_recurring=True)
        for habit in habits:
            update_habit_performance(habit)
        
        summary = get_habits_summary(request.user)
        serializer = HabitSummarySerializer(summary)
        return Response(serializer.data)


class HabitDetailView(APIView):
    """Get performance for a specific habit."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_habits_detail",
        summary="Get habit performance",
        responses={200: HabitPerformanceSerializer},
    )
    def get(self, request, task_id):
        """Get performance for a specific recurring task."""
        from .services import update_habit_performance
        from apps.tasks.models import Task
        
        try:
            task = Task.objects.get(id=task_id, user=request.user, is_recurring=True)
        except Task.DoesNotExist:
            return Response(
                {"error": "Recurring task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        perf = update_habit_performance(task)
        serializer = HabitPerformanceSerializer(perf)
        return Response(serializer.data)


# =============================================================================
# Goal Progress
# =============================================================================


class GoalProgressView(APIView):
    """
    Get progress stats for goals.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_goals_list",
        summary="Get goals progress",
        responses={200: GoalsSummarySerializer},
    )
    def get(self, request):
        """Get summary of all goals progress."""
        from .services import update_goal_progress
        from apps.goals.models import Goal
        
        # Update all goal progress
        goals = Goal.objects.filter(
            user=request.user,
            status__in=[Goal.Status.ACTIVE, Goal.Status.PLANNING],
        )
        for goal in goals:
            update_goal_progress(goal)
        
        summary = get_goals_summary(request.user)
        serializer = GoalsSummarySerializer(summary)
        return Response(serializer.data)


class GoalProgressDetailView(APIView):
    """Get progress for a specific goal."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_goals_detail",
        summary="Get goal progress",
        responses={200: GoalProgressSerializer},
    )
    def get(self, request, goal_id):
        """Get progress for a specific goal."""
        from .services import update_goal_progress
        from apps.goals.models import Goal
        
        try:
            goal = Goal.objects.get(id=goal_id, user=request.user)
        except Goal.DoesNotExist:
            return Response(
                {"error": "Goal not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        progress = update_goal_progress(goal)
        serializer = GoalProgressSerializer(progress)
        return Response(serializer.data)


# =============================================================================
# Personal Records
# =============================================================================


class PersonalRecordsView(APIView):
    """
    Get user's personal records.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_records_get",
        summary="Get personal records",
        responses={200: PersonalRecordsSummarySerializer},
    )
    def get(self, request):
        """Get all personal records."""
        records = get_user_records(request.user)
        serializer = PersonalRecordsSummarySerializer(records)
        return Response(serializer.data)


# =============================================================================
# Period Comparison
# =============================================================================


class WeekComparisonView(APIView):
    """Compare this week with last week."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_compare_week",
        summary="Compare weeks",
        responses={200: ComparisonResultSerializer},
    )
    def get(self, request):
        """Compare this week vs last week."""
        result = compare_periods(request.user, PeriodComparison.PeriodType.WEEK)
        serializer = ComparisonResultSerializer(result)
        return Response(serializer.data)


class MonthComparisonView(APIView):
    """Compare this month with last month."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_compare_month",
        summary="Compare months",
        responses={200: ComparisonResultSerializer},
    )
    def get(self, request):
        """Compare this month vs last month."""
        result = compare_periods(request.user, PeriodComparison.PeriodType.MONTH)
        serializer = ComparisonResultSerializer(result)
        return Response(serializer.data)


# =============================================================================
# Group Rankings
# =============================================================================


class GroupLeaderboardView(APIView):
    """Get leaderboard for a group."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_group_leaderboard",
        summary="Get group leaderboard",
        parameters=[
            OpenApiParameter(
                name="period",
                description="Period type: 'week' or 'month'",
                required=False,
                type=str,
                default="week",
            ),
        ],
        responses={200: GroupLeaderboardSerializer},
    )
    def get(self, request, group_id):
        """Get leaderboard for a specific group."""
        from apps.groups.models import Group, GroupMembership
        from .models import GroupRanking
        from .services import get_week_bounds, get_month_bounds
        
        # Check group access
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response(
                {"error": "Group not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check membership
        is_member = (
            group.owner == request.user or
            GroupMembership.objects.filter(
                group=group, user=request.user, is_active=True
            ).exists()
        )
        
        if not is_member and not group.is_public:
            return Response(
                {"error": "You are not a member of this group"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        period = request.query_params.get("period", "week")
        today = timezone.now().date()
        
        if period == "month":
            period_type = PeriodComparison.PeriodType.MONTH
            period_start, _ = get_month_bounds(today)
        else:
            period_type = PeriodComparison.PeriodType.WEEK
            period_start, _ = get_week_bounds(today)
        
        rankings = GroupRanking.objects.filter(
            group=group,
            period_type=period_type,
            period_start=period_start,
        ).select_related("user").order_by("rank")
        
        my_rank = rankings.filter(user=request.user).first()
        
        return Response({
            "group_id": group.id,
            "group_name": group.name,
            "period_type": period_type,
            "period_start": period_start,
            "rankings": GroupLeaderboardSerializer().to_representation(rankings)["rankings"] if rankings else [],
            "my_rank": GroupLeaderboardSerializer().fields["my_rank"].to_representation(my_rank) if my_rank else None,
        })


# =============================================================================
# Dashboard (combined stats)
# =============================================================================


class DashboardStatsView(APIView):
    """
    Get all stats for dashboard in one request.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Stats"],
        operation_id="stats_dashboard",
        summary="Get dashboard stats",
        description="Get combined stats: streak, today, this week, records, top habits, active goals",
        responses={200: DashboardStatsSerializer},
    )
    def get(self, request):
        """Get combined dashboard stats."""
        from .services import (
            update_goal_progress,
            update_habit_performance,
        )
        from apps.tasks.models import Task
        from apps.goals.models import Goal
        
        user = request.user
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        # Streak
        streak = get_or_create_streak(user)
        streak.check_streak_broken()
        
        # Today
        today_stats = update_daily_productivity(user, today)
        
        # This week
        week_summary = get_productivity_summary(user, week_start, today)
        
        # Personal records
        records = PersonalRecord.objects.filter(
            user=user,
            is_current=True,
        ).order_by("record_type")[:5]
        
        # Top habits (by consistency)
        habits = Task.objects.filter(user=user, is_recurring=True)[:5]
        for h in habits:
            update_habit_performance(h)
        
        top_habits = HabitPerformance.objects.filter(
            task__user=user,
        ).order_by("-consistency_rate")[:5]
        
        # Active goals
        goals = Goal.objects.filter(
            user=user,
            status=Goal.Status.ACTIVE,
        )[:5]
        for g in goals:
            update_goal_progress(g)
        
        active_goals = GoalProgress.objects.filter(
            goal__user=user,
            goal__status=Goal.Status.ACTIVE,
        ).order_by("-progress_percentage")[:5]
        
        return Response({
            "streak": UserStreakSerializer(streak).data,
            "today": DailyProductivitySerializer(today_stats).data,
            "this_week": ProductivitySummarySerializer(week_summary).data,
            "personal_records": PersonalRecordSerializer(records, many=True).data,
            "top_habits": HabitPerformanceSerializer(top_habits, many=True).data,
            "active_goals": GoalProgressSerializer(active_goals, many=True).data,
        })
