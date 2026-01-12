"""
Models for the Feedback app.

Handles user feedback, bug reports, and feature suggestions.
"""

from django.conf import settings
from django.db import models


class Feedback(models.Model):
    """
    Model for storing user feedback, suggestions, and bug reports.
    """

    class FeedbackType(models.TextChoices):
        """Types of feedback that users can submit."""

        BUG_REPORT = "bug_report", "Bug Report"
        SUGGESTION = "suggestion", "Suggestion"
        COMMENT = "comment", "General Comment"
        QUESTION = "question", "Question"

    class Status(models.TextChoices):
        """Status of the feedback item."""

        NEW = "new", "New"
        IN_REVIEW = "in_review", "In Review"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"
        WONT_FIX = "wont_fix", "Won't Fix"

    class Priority(models.TextChoices):
        """Priority level of the feedback (set by admin)."""

        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    # User who submitted the feedback
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedbacks",
        help_text="User who submitted this feedback",
    )

    # Feedback content
    feedback_type = models.CharField(
        max_length=20,
        choices=FeedbackType.choices,
        default=FeedbackType.COMMENT,
        help_text="Type of feedback",
    )
    title = models.CharField(
        max_length=200,
        help_text="Brief title/summary of the feedback",
    )
    message = models.TextField(
        help_text="Detailed description of the feedback",
    )

    # App context (optional but useful for debugging)
    app_version = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="App version when feedback was submitted",
    )
    device_info = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Device/OS information",
    )
    screen_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Screen/route where user was when submitting feedback",
    )

    # Admin-managed fields
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        help_text="Current status of this feedback",
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        blank=True,
        null=True,
        help_text="Priority level (set by admin)",
    )
    admin_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes from admin/developers",
    )
    resolved_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this feedback was resolved",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["feedback_type", "status"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"[{self.get_feedback_type_display()}] {self.title} - {self.user.email}"

    def mark_resolved(self):
        """Mark feedback as resolved."""
        from django.utils import timezone

        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])

