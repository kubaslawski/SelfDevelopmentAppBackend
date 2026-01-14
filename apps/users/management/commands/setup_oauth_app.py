"""
Management command to create OAuth2 application for the mobile app.
"""

from django.core.management.base import BaseCommand

# type: ignore
from oauth2_provider.models import Application


class Command(BaseCommand):
    """Create or update the OAuth2 application for the mobile app."""

    help = "Create or update OAuth2 application for Self Development App mobile client"

    def add_arguments(self, parser):
        parser.add_argument(
            "--client-id",
            type=str,
            default="sda-mobile-app",
            help="Client ID for the application",
        )
        parser.add_argument(
            "--expo-ip",
            type=str,
            help="Your local IP for Expo development (e.g., 192.168.33.11)",
        )

    def handle(self, *args, **options):
        client_id = options["client_id"]
        expo_ip = options.get("expo_ip")

        # Base redirect URIs
        redirect_uris = [
            # Production: custom scheme
            "selfdevelopmentapp://oauth/callback",
            # Development: Expo Go
            "exp://localhost:8081/--/oauth/callback",
            "exp://127.0.0.1:8081/--/oauth/callback",
        ]

        # Add custom Expo IP if provided
        if expo_ip:
            redirect_uris.append(f"exp://{expo_ip}:8081/--/oauth/callback")
            self.stdout.write(f"Adding Expo IP: {expo_ip}")

        # OAuth2 application settings for mobile app with PKCE
        app_defaults = {
            "name": "Self Development App Mobile",
            "client_type": Application.CLIENT_PUBLIC,  # Public client (mobile apps)
            "authorization_grant_type": Application.GRANT_AUTHORIZATION_CODE,
            # Redirect URIs for mobile app (space separated)
            "redirect_uris": " ".join(redirect_uris),
            "skip_authorization": False,  # Show authorization screen to confirm user identity
            # No client_secret for public clients (PKCE provides security)
            "client_secret": "",
            "algorithm": Application.NO_ALGORITHM,  # Using PKCE instead
        }

        app, created = Application.objects.update_or_create(
            client_id=client_id,
            defaults=app_defaults,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Created OAuth2 application"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Updated OAuth2 application"))

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.HTTP_INFO("OAuth2 Application Details:"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Name:              {app.name}")
        self.stdout.write(f"  Client ID:         {app.client_id}")
        self.stdout.write(f"  Client Type:       Public (mobile app)")
        self.stdout.write(f"  Grant Type:        Authorization Code + PKCE")
        self.stdout.write(f"  Redirect URI:      {app.redirect_uris}")
        self.stdout.write(f"  Skip Authorization: {app.skip_authorization}")
        self.stdout.write("=" * 60)
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("OAuth2 Endpoints:"))
        self.stdout.write("=" * 60)
        self.stdout.write("  Authorization:     /o/authorize/")
        self.stdout.write("  Token:             /o/token/")
        self.stdout.write("  UserInfo:          /o/userinfo/")
        self.stdout.write("  Discovery:         /o/.well-known/openid-configuration/")
        self.stdout.write("  Revoke:            /o/revoke_token/")
        self.stdout.write("=" * 60)
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "Note: This is a PUBLIC client. Authentication uses PKCE "
                "(Proof Key for Code Exchange) for security."
            )
        )
