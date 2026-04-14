"""URL configuration for users app."""

from django.urls import path

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    RegisterView,
    UserProfileView,
    VerifyEmailView,
)

app_name = "users"

urlpatterns = [
    # Authentication
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    # User profile
    path("users/me/", UserProfileView.as_view(), name="profile"),
    path("users/me/change-password/", ChangePasswordView.as_view(), name="change-password"),
]
