"""
Custom forms for email-based authentication.
"""

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """
    Authentication form that uses email instead of username.
    Used in OAuth2 authorization flow.
    """

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        ),
    )

    error_messages = {
        "invalid_login": "Please enter a correct email and password. "
        "Note that both fields may be case-sensitive.",
        "inactive": "This account is inactive.",
    }

    def clean(self):
        email = self.cleaned_data.get("username")  # username field contains email
        password = self.cleaned_data.get("password")

        if email is not None and password:
            self.user_cache = authenticate(
                self.request, username=email, password=password
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

