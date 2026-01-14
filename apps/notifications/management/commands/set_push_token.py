"""
Management command to manually set push token for a user.

Useful for testing when mobile app integration is not yet complete.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.notifications.services import get_or_create_preferences

User = get_user_model()


class Command(BaseCommand):
    help = "Set push notification token for a user"

    def add_arguments(self, parser):
        parser.add_argument(
            "push_token",
            type=str,
            help="Expo push token (e.g., ExponentPushToken[xxx])",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="kubaslawski@gmail.com",
            help="User email",
        )

    def handle(self, *args, **options):
        email = options["email"]
        push_token = options["push_token"]

        # Get user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"User {email} not found!"))
            return

        # Set push token
        prefs = get_or_create_preferences(user)
        prefs.push_token = push_token
        prefs.push_enabled = True
        prefs.notifications_enabled = True
        prefs.save()

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Push token set successfully!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  User: {email}")
        self.stdout.write(f"  Token: {push_token[:30]}...")
        self.stdout.write(f"  Push enabled: ✅")
        self.stdout.write(f"  Notifications enabled: ✅")
        self.stdout.write(self.style.SUCCESS("=" * 60))

