"""Custom authentication backend for email-based login."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that uses email instead of username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user by email and password.

        Note: Django's authenticate() passes email as 'username' parameter,
        so we accept it as username but treat it as email.
        Email comparison is case-insensitive.
        """
        email = kwargs.get("email") or username

        if email is None or password is None:
            return None

        # Normalize email to lowercase for case-insensitive comparison
        email = email.lower().strip()

        try:
            # Use iexact for case-insensitive email lookup
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
