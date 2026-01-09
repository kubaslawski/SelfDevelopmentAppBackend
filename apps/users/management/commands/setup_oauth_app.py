"""
Management command to create OAuth2 application for the mobile app.
"""

from django.core.management.base import BaseCommand
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

    def handle(self, *args, **options):
        client_id = options["client_id"]

        # OAuth2 application settings for mobile app with PKCE
        app_defaults = {
            "name": "Self Development App Mobile",
            "client_type": Application.CLIENT_PUBLIC,  # Public client (mobile apps)
            "authorization_grant_type": Application.GRANT_AUTHORIZATION_CODE,
            # Redirect URI for mobile app (custom scheme)
            "redirect_uris": "selfdevelopmentapp://oauth/callback",
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
