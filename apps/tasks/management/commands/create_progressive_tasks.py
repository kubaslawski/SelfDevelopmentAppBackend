"""
Management command to create progressive recurring tasks for all users.

Creates a task that starts on 01.01 of current year and has completions
for each day until today, with the target value increasing by 5 each day.
"""

from datetime import date, timedelta

from apps.tasks.models import Task, TaskCompletion
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Create progressive recurring tasks for all users (01.01 to today, +5 each day)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--unit-type",
            type=str,
            choices=["minutes", "hours", "count"],
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

    def handle(self, *args, **options):
        unit_type = options["unit_type"]
        start_value = options["start_value"]
        increment = options["increment"]
        task_title = options["task_title"]
        dry_run = options["dry_run"]

        # Calculate date range
        year_start = date(timezone.now().year, 1, 1)
        today = timezone.now().date()
        total_days = (today - year_start).days + 1

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.HTTP_INFO("Progressive Task Creator"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Task title:    {task_title}")
        self.stdout.write(f"  Unit type:     {unit_type}")
        self.stdout.write(f"  Start value:   {start_value}")
        self.stdout.write(f"  Increment:     +{increment} per day")
        self.stdout.write(f"  Date range:    {year_start} to {today}")
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

            # Create the task
            task = Task.objects.create(
                user=user,
                title=task_title,
                description=(
                    f"Progressive challenge starting with {start_value} "
                    f"and increasing by {increment} each day.\n\n"
                    f"Started: {year_start}\n"
                    f"Current target: {start_value + (total_days - 1) * increment}"
                ),
                status=Task.Status.IN_PROGRESS,
                priority=Task.Priority.HIGH,
                is_recurring=True,
                recurrence_period=Task.RecurrencePeriod.DAILY,
                recurrence_target_count=1,
                unit_type=unit_type,
                target_value=start_value,  # Initial target
                tags="progressive,challenge,daily",
            )

            self.stdout.write(self.style.SUCCESS(f"  Created task (ID: {task.id})"))

            # Create completions for each day
            completions_created = 0
            current_date = year_start

            while current_date <= today:
                day_number = (current_date - year_start).days + 1
                day_target = start_value + (day_number - 1) * increment

                # Create completion at noon of each day
                completed_at = timezone.make_aware(
                    timezone.datetime(
                        current_date.year, current_date.month, current_date.day, 12, 0, 0  # Noon
                    )
                )

                TaskCompletion.objects.create(
                    task=task,
                    completed_at=completed_at,
                    notes=f"Day {day_number}: Target {day_target} {unit_type}",
                    duration_minutes=day_target if unit_type == "minutes" else None,
                )

                completions_created += 1
                current_date += timedelta(days=1)

            # Update task target_value to current day's target
            final_target = start_value + (total_days - 1) * increment
            task.target_value = final_target
            task.save(update_fields=["target_value"])

            self.stdout.write(f"  Created {completions_created} completions")
            self.stdout.write(f"  Current target: {final_target} {unit_type}")
            self.stdout.write("")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Done!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        if not dry_run:
            self.stdout.write("")
            self.stdout.write("Example daily progression:")
            self.stdout.write(f"  Day 1 (Jan 1):  {start_value} {unit_type}")
            self.stdout.write(f"  Day 2 (Jan 2):  {start_value + increment} {unit_type}")
            self.stdout.write(f"  Day 3 (Jan 3):  {start_value + 2 * increment} {unit_type}")
            self.stdout.write("  ...")
            self.stdout.write(
                f"  Today (Day {total_days}): {start_value + (total_days - 1) * increment} {unit_type}"
            )
