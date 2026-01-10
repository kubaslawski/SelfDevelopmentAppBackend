"""
Management command to create progressive recurring tasks for all users.

Creates a task with completions where the target value increases each day.
"""

from datetime import date, datetime, timedelta

from apps.tasks.models import Task, TaskCompletion
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Create progressive recurring tasks for all users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--unit-type",
            type=str,
            choices=[
                "minutes",
                "hours",
                "count",
                "pages",
                "kilometers",
                "meters",
                "calories",
                "steps",
            ],
            default="count",
            help="Unit type for the task (default: count)",
        )
        parser.add_argument(
            "--start-value",
            type=int,
            default=5,
            help="Starting value on day 1 (default: 5)",
        )
        parser.add_argument(
            "--increment",
            type=int,
            default=5,
            help="Daily increment (default: 5)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=10,
            help="Number of days to create completions for (default: 10)",
        )
        parser.add_argument(
            "--task-title",
            type=str,
            default="Progressive Challenge",
            help="Title for the task",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating",
        )
        parser.add_argument(
            "--delete-existing",
            action="store_true",
            help="Delete existing progressive tasks before creating new ones",
        )

    def handle(self, *args, **options):
        unit_type = options["unit_type"]
        start_value = options["start_value"]
        increment = options["increment"]
        total_days = options["days"]
        task_title = options["task_title"]
        dry_run = options["dry_run"]
        delete_existing = options["delete_existing"]

        # Delete existing tasks if requested
        if delete_existing and not dry_run:
            existing_tasks = Task.objects.filter(title=task_title, is_recurring=True)
            count = existing_tasks.count()
            if count > 0:
                # This will also delete related completions via CASCADE
                existing_tasks.delete()
                self.stdout.write(
                    self.style.WARNING(f"Deleted {count} existing '{task_title}' tasks")
                )
                self.stdout.write("")

        # Calculate date range (last N days ending today)
        today = timezone.now().date()
        start_date = today - timedelta(days=total_days - 1)

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.HTTP_INFO("Progressive Task Creator"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Task title:    {task_title}")
        self.stdout.write(f"  Unit type:     {unit_type}")
        self.stdout.write(f"  Start value:   {start_value}")
        self.stdout.write(f"  Increment:     +{increment} per day")
        self.stdout.write(f"  Date range:    {start_date} to {today}")
        self.stdout.write(f"  Total days:    {total_days}")
        self.stdout.write(f"  Final value:   {start_value + (total_days - 1) * increment}")
        self.stdout.write("=" * 60)
        self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
            self.stdout.write("")

        # Get all users (excluding superusers if you want)
        users = User.objects.filter(is_active=True)

        if not users.exists():
            self.stdout.write(self.style.ERROR("No active users found!"))
            return

        self.stdout.write(f"Found {users.count()} active users")
        self.stdout.write("")

        for user in users:
            self.stdout.write(f"Processing user: {user.email}")

            # Check if task already exists
            existing_task = Task.objects.filter(
                user=user,
                title=task_title,
                is_recurring=True,
            ).first()

            if existing_task:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Task already exists (ID: {existing_task.id}), skipping..."
                    )
                )
                continue

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f"  Would create task with {total_days} completions")
                )
                continue

            # Calculate final target
            final_target = start_value + (total_days - 1) * increment

            # Create the task
            task = Task.objects.create(
                user=user,
                title=task_title,
                description=(
                    f"Progressive challenge starting with {start_value} {unit_type} "
                    f"and increasing by {increment} each day.\n\n"
                    f"Started: {start_date}\n"
                    f"Current target: {final_target} {unit_type}"
                ),
                status=Task.Status.IN_PROGRESS,
                priority=Task.Priority.HIGH,
                is_recurring=True,
                recurrence_period=Task.RecurrencePeriod.DAILY,
                recurrence_target_count=1,
                unit_type=unit_type,
                target_value=final_target,
                tags="progressive,challenge,daily",
            )

            self.stdout.write(self.style.SUCCESS(f"  Created task (ID: {task.id})"))

            # Create completions for each day
            completions_created = 0
            current_date = start_date

            for day_number in range(1, total_days + 1):
                day_target = start_value + (day_number - 1) * increment

                # Create completion at noon of each day
                completed_at = timezone.make_aware(
                    datetime(current_date.year, current_date.month, current_date.day, 12, 0, 0)
                )

                TaskCompletion.objects.create(
                    task=task,
                    completed_at=completed_at,
                    completed_value=day_target,
                    notes=f"Day {day_number}",
                    duration_minutes=day_target if unit_type == "minutes" else None,
                )

                completions_created += 1
                current_date += timedelta(days=1)

            self.stdout.write(f"  Created {completions_created} completions")
            self.stdout.write(f"  Progression: {start_value} → {final_target} {unit_type}")
            self.stdout.write("")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Done!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        if not dry_run:
            self.stdout.write("")
            self.stdout.write("Daily progression:")
            for day in range(1, min(total_days + 1, 6)):  # Show first 5 days
                day_date = start_date + timedelta(days=day - 1)
                day_value = start_value + (day - 1) * increment
                self.stdout.write(f"  Day {day} ({day_date}): {day_value} {unit_type}")
            if total_days > 5:
                self.stdout.write("  ...")
                final_value = start_value + (total_days - 1) * increment
                self.stdout.write(f"  Day {total_days} ({today}): {final_value} {unit_type}")
