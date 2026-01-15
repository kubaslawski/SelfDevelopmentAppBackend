"""URL configuration for Stats app."""

from django.urls import path

from .views import (
    DailyProductivityView,
    DashboardStatsView,
    GoalProgressDetailView,
    GoalProgressView,
    GroupLeaderboardView,
    HabitDetailView,
    HabitPerformanceView,
    MonthComparisonView,
    PersonalRecordsView,
    TodayStatsView,
    UserStreakView,
    WeekComparisonView,
)

app_name = "stats"

urlpatterns = [
    # Dashboard (all stats combined)
    path("stats/dashboard/", DashboardStatsView.as_view(), name="dashboard"),
    
    # Streak
    path("stats/streak/", UserStreakView.as_view(), name="streak"),
    
    # Daily productivity
    path("stats/productivity/", DailyProductivityView.as_view(), name="productivity"),
    path("stats/today/", TodayStatsView.as_view(), name="today"),
    
    # Habits
    path("stats/habits/", HabitPerformanceView.as_view(), name="habits"),
    path("stats/habits/<int:task_id>/", HabitDetailView.as_view(), name="habit-detail"),
    
    # Goals
    path("stats/goals/", GoalProgressView.as_view(), name="goals"),
    path("stats/goals/<int:goal_id>/", GoalProgressDetailView.as_view(), name="goal-detail"),
    
    # Personal records
    path("stats/records/", PersonalRecordsView.as_view(), name="records"),
    
    # Comparisons
    path("stats/compare/week/", WeekComparisonView.as_view(), name="compare-week"),
    path("stats/compare/month/", MonthComparisonView.as_view(), name="compare-month"),
    
    # Group leaderboard
    path("stats/groups/<int:group_id>/leaderboard/", GroupLeaderboardView.as_view(), name="group-leaderboard"),
]

