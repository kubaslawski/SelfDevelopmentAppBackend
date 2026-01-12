"""
Admin configuration for Goals app.
"""

from django.contrib import admin

from .models import Goal, Milestone, MilestoneTaskLink


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0
    fields = ["title", "status", "order", "target_date"]
    readonly_fields = ["created_at"]
    ordering = ["order"]


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "category",
        "status",
        "target_date",
        "progress_percentage",
        "created_at",
    ]
    list_filter = ["status", "category", "created_at"]
    search_fields = ["title", "description", "user__email"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "completed_at",
        "plan_generated_at",
        "progress_percentage",
    ]
    inlines = [MilestoneInline]

    fieldsets = (
        (None, {
            "fields": ("title", "description", "user", "category", "status"),
        }),
        ("Timeline", {
            "fields": ("start_date", "target_date", "completed_at"),
        }),
        ("AI Planning", {
            "fields": (
                "planning_questions",
                "planning_answers",
                "llm_generated_plan",
                "plan_generated_at",
            ),
            "classes": ("collapse",),
        }),
        ("Motivation & Tips", {
            "fields": ("motivation", "potential_obstacles", "tips"),
            "classes": ("collapse",),
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at", "progress_percentage"),
            "classes": ("collapse",),
        }),
    )

    def progress_percentage(self, obj):
        return f"{obj.progress_percentage}%"
    progress_percentage.short_description = "Progress"


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "goal",
        "status",
        "order",
        "target_date",
        "is_overdue",
    ]
    list_filter = ["status", "goal__category"]
    search_fields = ["title", "description", "goal__title"]
    readonly_fields = ["created_at", "updated_at", "completed_at"]
    ordering = ["goal", "order"]

    fieldsets = (
        (None, {
            "fields": ("goal", "title", "description", "status", "order"),
        }),
        ("Timeline", {
            "fields": ("target_date", "completed_at"),
        }),
        ("Details", {
            "fields": ("requirements", "notes", "suggested_tasks"),
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(MilestoneTaskLink)
class MilestoneTaskLinkAdmin(admin.ModelAdmin):
    list_display = ["milestone", "task", "created_at"]
    list_filter = ["milestone__goal", "milestone__status"]
    search_fields = ["milestone__title", "task__title"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["milestone", "task"]

