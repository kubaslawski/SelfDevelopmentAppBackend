"""Views for user authentication and management."""

from django.contrib.auth import get_user_model, login, logout
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

User = get_user_model()


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

        return Response(
            {
                "message": "User registered successfully.",
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


@extend_schema_view(
    post=extend_schema(
        summary="Logout",
        description="Logout the current user and destroy the session.",
        tags=["Authentication"],
        request=None,  # No request body needed
    )
)
class LogoutView(APIView):
    """Logout the current user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )


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
