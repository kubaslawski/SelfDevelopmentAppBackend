"""
Management command to seed the database with sample users and tasks.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.tasks.models import Task

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with sample users and tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-if-exists",
            action="store_true",
            help="Skip seeding if data already exists",
        )

    def handle(self, *args, **options):
        skip_if_exists = options.get("skip_if_exists", False)

        if skip_if_exists and User.objects.exists():
            self.stdout.write(self.style.WARNING("Data already exists. Skipping seed."))
            return

        self.stdout.write("Seeding database...")

        # Create superusers
        self._create_superuser("admin@admin.pl", "admin", "Admin", "User")
        self._create_superuser("kubaslawski@gmail.com", "Grzejnik12!", "Kuba", "Ślawski")

    def _create_superuser(self, email, password, first_name, last_name):
        """Create superuser if not exists."""
        if User.objects.filter(email=email).exists():
            self.stdout.write(f"Superuser {email} already exists.")
            return User.objects.get(email=email)

        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        self.stdout.write(self.style.SUCCESS(f"Created superuser: {email}"))
        return user

    def _create_user(self, user_data):
        """Create a regular user."""
        email = user_data["email"]
        if User.objects.filter(email=email).exists():
            self.stdout.write(f"User {email} already exists.")
            return User.objects.get(email=email)

        user = User.objects.create_user(
            email=email,
            password="password123",
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
        )
        self.stdout.write(self.style.SUCCESS(f"Created user: {email}"))
        return user

    def _create_tasks(self, user, tasks_data):
        """Create tasks for a user."""
        now = timezone.now()
        statuses = ["todo", "in_progress", "todo", "in_progress", "todo"]

        for i, (
            title,
            description,
            priority,
            recurrence_period,
            recurrence_count,
            duration,
            tags,
        ) in enumerate(tasks_data):
            Task.objects.create(
                user=user,
                title=title,
                description=description,
                priority=priority,
                status=statuses[i],
                is_recurring=recurrence_period is not None,
                recurrence_period=recurrence_period,
                recurrence_target_count=recurrence_count,
                estimated_duration=duration,
                tags=tags,
                due_date=now + timezone.timedelta(days=(i + 1) * 7),
            )
        self.stdout.write(f"  Created {len(tasks_data)} tasks for {user.email}")
