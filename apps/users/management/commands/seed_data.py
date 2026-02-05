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
        self._create_superuser("kubaslawski@gmail.com", "admin", "Kuba", "Sławski")

        # Create regular users with tasks
        users_data = [
            {
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "tasks": [
                    (
                        "Morning stretching routine",
                        "Start each day with 10 minutes of stretching.",
                        "low",
                        "daily",
                        1,
                        10,
                        "fitness, morning",
                    ),
                    (
                        "Complete strength training",
                        "Full body workout: squats, deadlifts, bench press.",
                        "medium",
                        "weekly",
                        3,
                        60,
                        "gym, strength",
                    ),
                    (
                        "Run 5K",
                        "Build cardiovascular endurance by running 5 kilometers.",
                        "medium",
                        "weekly",
                        2,
                        30,
                        "running, cardio",
                    ),
                    (
                        "Track daily calories",
                        "Log all meals to maintain nutrition awareness.",
                        "high",
                        "daily",
                        1,
                        5,
                        "nutrition, health",
                    ),
                    (
                        "Train for half-marathon",
                        "Follow 12-week training plan to run 21.1km.",
                        "urgent",
                        None,
                        None,
                        90,
                        "marathon, ambitious",
                    ),
                ],
            },
            {
                "email": "jane@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "tasks": [
                    (
                        "Solve coding challenge",
                        "Complete a LeetCode problem to sharpen algorithms.",
                        "medium",
                        "daily",
                        1,
                        30,
                        "coding, practice",
                    ),
                    (
                        "Contribute to open source",
                        "Submit a PR to an open source project on GitHub.",
                        "medium",
                        "weekly",
                        1,
                        60,
                        "opensource, github",
                    ),
                    (
                        "Study AWS certification",
                        "Complete one module of AWS Solutions Architect course.",
                        "high",
                        "weekly",
                        3,
                        45,
                        "aws, certification",
                    ),
                    (
                        "Write technical blog post",
                        "Share knowledge about a problem you solved.",
                        "high",
                        "monthly",
                        2,
                        120,
                        "writing, blog",
                    ),
                    (
                        "Build SaaS product MVP",
                        "Create a complete product from idea to production.",
                        "urgent",
                        None,
                        None,
                        480,
                        "saas, entrepreneurship",
                    ),
                ],
            },
            {
                "email": "mike@example.com",
                "first_name": "Mike",
                "last_name": "Wilson",
                "tasks": [
                    (
                        "Review Anki flashcards",
                        "Spend 10 minutes reviewing vocabulary using spaced repetition.",
                        "low",
                        "daily",
                        1,
                        10,
                        "vocabulary, anki",
                    ),
                    (
                        "Listen to language podcast",
                        "Immerse yourself by listening to native content.",
                        "low",
                        "daily",
                        1,
                        20,
                        "listening, immersion",
                    ),
                    (
                        "Practice with language partner",
                        "Have a 30-minute conversation with a native speaker.",
                        "medium",
                        "weekly",
                        2,
                        30,
                        "speaking, practice",
                    ),
                    (
                        "Write journal in target language",
                        "Practice writing by describing your day.",
                        "high",
                        "daily",
                        1,
                        15,
                        "writing, journal",
                    ),
                    (
                        "Pass B2 certification exam",
                        "Prepare for and pass official language proficiency exam.",
                        "urgent",
                        None,
                        None,
                        120,
                        "certification, fluency",
                    ),
                ],
            },
            {
                "email": "sarah@example.com",
                "first_name": "Sarah",
                "last_name": "Jones",
                "tasks": [
                    (
                        "Morning meditation",
                        "Start the day with guided meditation using Headspace.",
                        "medium",
                        "daily",
                        1,
                        15,
                        "meditation, mindfulness",
                    ),
                    (
                        "Write gratitude journal",
                        "Write down three things you are grateful for today.",
                        "low",
                        "daily",
                        1,
                        5,
                        "gratitude, journaling",
                    ),
                    (
                        "Practice yoga session",
                        "Combine physical movement with mindfulness.",
                        "medium",
                        "weekly",
                        3,
                        45,
                        "yoga, movement",
                    ),
                    (
                        "Digital detox hour",
                        "Spend one hour without any screens.",
                        "high",
                        "daily",
                        1,
                        60,
                        "detox, presence",
                    ),
                    (
                        "Complete 30-day meditation challenge",
                        "Build solid meditation practice with 30 consecutive days.",
                        "urgent",
                        None,
                        None,
                        450,
                        "challenge, habit",
                    ),
                ],
            },
            {
                "email": "david@example.com",
                "first_name": "David",
                "last_name": "Brown",
                "tasks": [
                    (
                        "Daily sketch practice",
                        "Draw anything for 15 minutes - people, objects, or abstract.",
                        "low",
                        "daily",
                        1,
                        15,
                        "drawing, sketch",
                    ),
                    (
                        "Study art from masters",
                        "Analyze works by famous artists - composition, color, technique.",
                        "medium",
                        "weekly",
                        1,
                        45,
                        "study, masters",
                    ),
                    (
                        "Work on larger art piece",
                        "Dedicate time to ambitious artwork that takes multiple sessions.",
                        "medium",
                        "weekly",
                        3,
                        90,
                        "artwork, project",
                    ),
                    (
                        "Share art on social media",
                        "Post your work on Instagram to build audience.",
                        "high",
                        "weekly",
                        2,
                        15,
                        "social, sharing",
                    ),
                    (
                        "Prepare portfolio for gallery",
                        "Curate best work for exhibition opportunities.",
                        "urgent",
                        None,
                        None,
                        180,
                        "portfolio, gallery",
                    ),
                ],
            },
        ]

        for user_data in users_data:
            user = self._create_user(user_data)
            self._create_tasks(user, user_data["tasks"])

        # Summary
        user_count = User.objects.count()
        task_count = Task.objects.count()

        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Seed data created successfully!"))
        self.stdout.write(self.style.SUCCESS(f"Users: {user_count} (including 2 superusers)"))
        self.stdout.write(self.style.SUCCESS(f"Tasks: {task_count}"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Superusers:"))
        self.stdout.write(self.style.SUCCESS("  - admin@admin.pl / admin"))
        self.stdout.write(self.style.SUCCESS("  - kubaslawski@gmail.com / admin"))
        self.stdout.write(self.style.SUCCESS("Regular users: password123"))
        self.stdout.write(self.style.SUCCESS("=" * 50))

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


