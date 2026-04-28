"""Views for user authentication and management."""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils.encoding import force_str
from django.utils.html import escape
from django.utils.http import urlencode, urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    ChangePasswordSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def _build_email_verification_link(user):
    """HTTPS link to this API — opens in browser and activates the account (GET)."""
    uid = urlsafe_base64_encode(str(user.pk).encode("utf-8"))
    token = default_token_generator.make_token(user)
    query = urlencode({"uid": uid, "token": token})
    base = settings.PUBLIC_API_BASE_URL.rstrip("/")
    return f"{base}/api/v1/auth/verify-email/?{query}"


def _perform_email_verification(uid, token):
    """
    Returns (outcome, message_for_json) where outcome is:
    missing_params | invalid_link | invalid_token | already_verified | success
    """
    if not uid or not token:
        return "missing_params", "Must include uid and token."

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return "invalid_link", "Invalid verification link."

    if user.is_active:
        return "already_verified", "Email already verified."

    if not default_token_generator.check_token(user, token):
        return "invalid_token", "Verification link is invalid or expired."

    user.is_active = True
    user.save(update_fields=["is_active"])
    logger.info("Email verified for user %s", user.email)
    return "success", "Email verified successfully. You can now sign in."


def _verification_html_page(outcome, _json_message):
    """Simple HTML for GET /verify-email/ (clicked from email)."""
    app_link = getattr(settings, "EMAIL_VERIFICATION_APP_DEEP_LINK", "selfdevelopmentapp://login")

    if outcome == "missing_params":
        title = "Niepełny link"
        body = "Brakuje parametrów weryfikacji. Użyj pełnego linku z wiadomości e-mail."
        ok = False
    elif outcome == "invalid_link":
        title = "Nieprawidłowy link"
        body = "Ten link potwierdzający jest nieprawidłowy lub został już użyty w innej formie."
        ok = False
    elif outcome == "invalid_token":
        title = "Link wygasł lub jest nieprawidłowy"
        body = "Poproś o nową rejestrację lub skontaktuj się z pomocą, jeśli problem się powtarza."
        ok = False
    elif outcome == "already_verified":
        title = "E-mail już potwierdzony"
        body = "Możesz zalogować się w aplikacji Verely."
        ok = True
    else:  # success
        title = "Konto aktywowane"
        body = "Adres e-mail został potwierdzony. Możesz zalogować się w aplikacji Verely."
        ok = True

    color = "#15803d" if ok else "#b91c1c"
    app_block = ""
    if ok:
        app_block = (
            f'<p style="margin-top:1.5rem"><a href="{escape(app_link)}" '
            'style="display:inline-block;padding:0.6rem 1rem;background:#111827;color:#fff;'
            'text-decoration:none;border-radius:8px;">Otwórz aplikację Verely</a></p>'
        )

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} — Verely</title>
</head>
<body style="font-family:system-ui,-apple-system,sans-serif;max-width:28rem;margin:2rem auto;padding:0 1rem;line-height:1.5;color:#111827;">
  <h1 style="color:{color};font-size:1.25rem;">{escape(title)}</h1>
  <p>{escape(body)}</p>
  {app_block}
</body>
</html>"""
    return HttpResponse(html, content_type="text/html; charset=utf-8")


def _send_verification_email(user):
    verification_link = _build_email_verification_link(user)
    subject = "Potwierdź swój adres e-mail w Verely"
    message = (
        "Dziękujemy za rejestrację w Verely.\n\n"
        "Aby aktywować konto, otwórz w przeglądarce poniższy link (kliknij lub skopiuj do paska adresu):\n"
        f"{verification_link}\n\n"
        "Po potwierdzeniu możesz zalogować się w aplikacji Verely.\n\n"
        "Jeśli nie zakładałeś konta, zignoruj tę wiadomość."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


@extend_schema_view(
    post=extend_schema(
        summary="Register new user",
        description="Create a new user account with email and password.",
        tags=["Authentication"],
    )
)
class RegisterView(generics.CreateAPIView):
    """Register a new user with email and password."""

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            _send_verification_email(user)
        except Exception:
            # Don't 500 the registration if SMTP is misconfigured or unreachable.
            # The user can request a resend; we still want the account persisted.
            logger.exception("Failed to send verification email to %s", user.email)

        return Response(
            {
                "message": (
                    "User registered successfully. "
                    "Please confirm your email address before signing in."
                ),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    post=extend_schema(
        summary="Login with email and password",
        description="Authenticate user with email and password. Creates a session.",
        tags=["Authentication"],
    )
)
class LoginView(APIView):
    """Login with email and password."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        login(request, user)

        return Response(
            {
                "message": "Login successful.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Logout the current user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Logout",
        description="Logout the current user and destroy the session.",
        tags=["Authentication"],
        request=None,
        responses={200: None},
    )
    def post(self, request):
        logout(request)
        return Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Confirm email address (link from email)",
        description=(
            "Opens in browser from the registration email; activates the account. "
            "Query parameters: uid, token."
        ),
        parameters=[
            OpenApiParameter(
                name="uid",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Base64-encoded user id",
            ),
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Verification token from email",
            ),
        ],
        tags=["Authentication"],
        responses={200: None},
    ),
    post=extend_schema(
        summary="Confirm email address (JSON)",
        description=(
            "Same verification as GET, for API clients (e.g. mobile app). "
            "Body: uid, token."
        ),
        tags=["Authentication"],
        request=EmailVerificationSerializer,
    ),
)
class VerifyEmailView(APIView):
    """Verify email address and activate account (GET = browser link, POST = JSON)."""

    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer

    def get(self, request):
        uid = request.query_params.get("uid")
        token = request.query_params.get("token")
        outcome, msg = _perform_email_verification(uid, token)
        return _verification_html_page(outcome, msg)

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        outcome, msg = _perform_email_verification(uid, token)

        if outcome in ("success", "already_verified"):
            return Response({"message": msg}, status=status.HTTP_200_OK)
        return Response({"message": msg}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary="Get current user profile",
        description="Returns the authenticated user's profile information.",
        tags=["User Profile"],
    ),
    put=extend_schema(
        summary="Update user profile",
        description="Update the authenticated user's profile information.",
        tags=["User Profile"],
    ),
    patch=extend_schema(
        summary="Partially update user profile",
        description="Partially update the authenticated user's profile information.",
        tags=["User Profile"],
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update the authenticated user's profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


@extend_schema_view(
    post=extend_schema(
        summary="Change password",
        description="Change the authenticated user's password.",
        tags=["User Profile"],
        request=ChangePasswordSerializer,
    )
)
class ChangePasswordView(APIView):
    """Change password for the authenticated user."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )
