"""
Management command to test push notifications.

Creates test notifications and sends them at regular intervals.
Useful for testing the notification system end-to-end.
"""

import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import (
    get_or_create_preferences,
    send_push_notification,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Create and send test notifications to a specific user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            default="kubaslawski@gmail.com",
            help="User email to send notifications to",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=300,  # 5 minutes
            help="Interval between notifications in seconds (default: 300 = 5 min)",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of notifications to send (default: 10)",
        )
        parser.add_argument(
            "--immediate",
            action="store_true",
            help="Send first notification immediately",
        )

    def handle(self, *args, **options):
        email = options["email"]
        interval = options["interval"]
        count = options["count"]
        immediate = options["immediate"]

        # Get user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"User {email} not found!"))
            return

        # Check if user has push token
        prefs = get_or_create_preferences(user)
        if not prefs.push_token:
            self.stderr.write(
                self.style.WARNING(
                    f"User {email} has no push token registered!\n"
                    "Register token first via mobile app."
                )
            )
            self.stdout.write(
                "Continuing anyway - notifications will be created but not sent."
            )

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Test Notification Runner"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  User: {email}")
        self.stdout.write(f"  Push token: {'✅ Set' if prefs.push_token else '❌ Not set'}")
        self.stdout.write(f"  Interval: {interval} seconds ({interval // 60} min)")
        self.stdout.write(f"  Count: {count} notifications")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        # Test messages with different notification types
        test_messages = [
            # (title, body, notification_type)
            ("Przypomnienie o zadaniu", "Nie zapomnij o swoich celach na dziś!", "task_reminder"),
            ("Zbliża się deadline!", "Masz tylko 1 godzinę na ukończenie zadania.", "deadline_warning"),
            ("Świetna robota!", "Ukończyłeś wszystkie zadania na dziś!", "congratulations"),
            ("Nowe osiągnięcie!", "Zdobyłeś odznakę 'Produktywny Tydzień'!", "achievement"),
            ("7 dni z rzędu!", "Utrzymujesz świetną passę - tak trzymaj!", "streak"),
            ("Może spróbujesz...", "Rozważ podzielenie dużego zadania na mniejsze.", "suggestion"),
            ("Porada dnia", "Zacznij dzień od najtrudniejszego zadania.", "tip"),
            ("Dzienny przegląd", "Masz 3 zadania do wykonania na dziś.", "daily_reminder"),
            ("Uwaga!", "Niektóre zadania są przeterminowane.", "warning"),
            ("Aktualizacja", "Dodano nową funkcję w aplikacji.", "info"),
        ]

        for i in range(count):
            title, body, notif_type = test_messages[i % len(test_messages)]
            title = f"{title} ({i + 1}/{count})"

            # Calculate when to send
            if immediate and i == 0:
                scheduled_for = timezone.now()
            else:
                wait_time = interval if i > 0 or not immediate else 0
                scheduled_for = timezone.now() + timedelta(seconds=wait_time * i)

            # Create notification with specific type
            notification = Notification.objects.create(
                user=user,
                notification_type=notif_type,
                title=title,
                body=body,
                scheduled_for=scheduled_for,
                reminder_key=f"test_{timezone.now().timestamp()}_{i}",
                status=Notification.Status.PENDING,
            )

            self.stdout.write(f"[{i + 1}/{count}] Created: {title}")

            if immediate and i == 0:
                # Send immediately
                self.stdout.write("  → Sending immediately...")
                success = send_push_notification(notification)
                if success:
                    self.stdout.write(self.style.SUCCESS("  ✅ Sent!"))
                else:
                    self.stdout.write(self.style.ERROR("  ❌ Failed to send"))
            else:
                self.stdout.write(f"  → Scheduled for: {scheduled_for.strftime('%H:%M:%S')}")

            # Wait between notifications (except for the last one)
            if i < count - 1 and not options.get("no_wait"):
                self.stdout.write(f"\n⏳ Waiting {interval} seconds...\n")
                time.sleep(interval)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS(f"Done! Created {count} test notifications."))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write("The pending notifications will be sent by Celery worker.")
        self.stdout.write("Check worker logs: docker-compose logs -f celery-worker")

