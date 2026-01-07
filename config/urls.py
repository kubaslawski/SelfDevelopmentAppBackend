"""
URL configuration for SelfDevelopmentAppBackend project.
"""

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
    # JWT Token endpoints (using email)
    path("api/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # API v1 - Authentication
    path("api/v1/", include("apps.users.urls")),
    # API v1 - Tasks
    path("api/v1/", include("apps.tasks.urls")),
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
