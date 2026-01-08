"""
Custom OAuth2 Validator for OpenID Connect support.
Provides user claims for ID tokens.
"""

from oauth2_provider.oauth2_validators import OAuth2Validator


class CustomOAuth2Validator(OAuth2Validator):
    """
    Custom OAuth2 validator that adds OpenID Connect claims
    and supports email-based authentication.
    """

    # Define OIDC claims
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope
    oidc_claim_scope.update(
        {
            "profile": [
                "name",
                "given_name",
                "family_name",
                "preferred_username",
                "updated_at",
            ],
            "email": [
                "email",
                "email_verified",
            ],
        }
    )

    def get_additional_claims(self, request):
        """
        Return additional claims for the ID token.
        Called when 'openid' scope is requested.
        """
        user = request.user
        claims = {}

        if "profile" in request.scopes:
            claims.update(
                {
                    "name": user.get_full_name() or user.email,
                    "given_name": user.first_name,
                    "family_name": user.last_name,
                    "preferred_username": user.email,
                    "updated_at": int(user.date_joined.timestamp()) if user.date_joined else None,
                }
            )

        if "email" in request.scopes:
            claims.update(
                {
                    "email": user.email,
                    "email_verified": user.is_active,  # Treat active as verified
                }
            )

        return claims

    def get_userinfo_claims(self, request):
        """
        Return claims for the userinfo endpoint.
        """
        claims = super().get_userinfo_claims(request)

        user = request.user
        claims.update(
            {
                "sub": str(user.id),
                "name": user.get_full_name() or user.email,
                "given_name": user.first_name,
                "family_name": user.last_name,
                "preferred_username": user.email,
                "email": user.email,
                "email_verified": user.is_active,
            }
        )

        return claims

    def validate_user(self, username, password, client, request, *args, **kwargs):
        """
        Validate username (email) and password for Resource Owner Password Grant.
        Note: This grant type is discouraged for mobile apps, use Authorization Code + PKCE instead.
        """
        from django.contrib.auth import authenticate

        # Authenticate using email as username
        user = authenticate(username=username, password=password)

        if user is not None and user.is_active:
            request.user = user
            return True

        return False
