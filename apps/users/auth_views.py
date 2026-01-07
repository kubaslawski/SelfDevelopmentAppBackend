"""
Custom authentication views for email-based login.
Used in OAuth2 authorization flow.
"""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

from .forms import EmailAuthenticationForm


class EmailLoginView(LoginView):
    """
    Login view that uses email instead of username.
    """

    template_name = "registration/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        """Redirect to next URL or home."""
        return self.request.GET.get("next") or reverse_lazy("admin:index")


class EmailLogoutView(LogoutView):
    """
    Logout view.
    """

    next_page = reverse_lazy("email_login")

