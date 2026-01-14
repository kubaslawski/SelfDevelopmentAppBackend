"""
URL configuration for SelfDevelopmentAppBackend project.
"""

from apps.users.auth_views import EmailLoginView, EmailLogoutView
from apps.users.serializers import EmailTokenObtainPairSerializer
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


class EmailTokenObtainPairView(TokenObtainPairView):
    """Token view that uses email instead of username."""

    serializer_class = EmailTokenObtainPairSerializer


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # =========================================================================
    # Authentication (Email-based login for OAuth flow)
    # =========================================================================
    path("accounts/login/", EmailLoginView.as_view(), name="email_login"),
    path("accounts/logout/", EmailLogoutView.as_view(), name="email_logout"),
    # =========================================================================
    # OAuth 2.0 + OpenID Connect (Authorization Code + PKCE)
    # =========================================================================
    # OAuth2 Provider endpoints:
    # - /o/authorize/          - Authorization endpoint (user login in browser)
    # - /o/token/              - Token endpoint (exchange code for tokens)
    # - /o/revoke_token/       - Revoke token endpoint
    # - /o/introspect/         - Token introspection
    # - /o/userinfo/           - OIDC UserInfo endpoint
    # - /o/.well-known/openid-configuration/ - OIDC discovery
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    # JWT Token endpoints (legacy, still supported)
    path("api/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # API v1 - Authentication
    path("api/v1/", include("apps.users.urls")),
    # API v1 - Tasks
    path("api/v1/", include("apps.tasks.urls")),
    # API v1 - Feedback
    path("api/v1/", include("apps.feedback.urls")),
    # API v1 - Goals
    path("api/v1/", include("apps.goals.urls")),
    # API v1 - Notifications
    path("api/v1/", include("apps.notifications.urls")),
    # API v1 - Groups
    path("api/v1/", include("apps.groups.urls")),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # DRF browsable API auth
    path("api-auth/", include("rest_framework.urls")),
]

# Debug toolbar (only in DEBUG mode)
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
