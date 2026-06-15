"""
Accounts views: Register, Login, Logout, Verify Email, Password Reset.
"""

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema

from .models import EmailVerificationToken, PasswordResetToken
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


class AuthRateThrottle(AnonRateThrottle):
    rate = "5/minute"
    scope = "auth"


@extend_schema(tags=["Authentication"])
class RegisterView(generics.CreateAPIView):
    """Register a new user. Sends email verification link."""

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        try:
            token_obj = user.email_verification_token
            verification_url = f"{settings.FRONTEND_URL}/verify-email/{token_obj.token}"
            send_mail(
                subject="Verify your ExpenseFlow account",
                message=f"Hi {user.first_name},\n\nClick to verify: {verification_url}\n\nThis link expires in 24 hours.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass  # Don't block registration if email fails

        return Response(
            {
                "message": "Registration successful. Please check your email to verify your account.",
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Authentication"])
class LoginView(TokenObtainPairView):
    """Login with email + password. Returns JWT access + refresh tokens."""

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]


@extend_schema(tags=["Authentication"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout: Blacklists the refresh token."""
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required.", "code": "MISSING_REFRESH_TOKEN"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": "Invalid token.", "code": "INVALID_TOKEN"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@extend_schema(tags=["Authentication"])
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email_view(request, token):
    """Verify email using token from verification email."""
    try:
        token_obj = EmailVerificationToken.objects.get(token=token)
    except EmailVerificationToken.DoesNotExist:
        return Response(
            {"error": "Invalid verification token.", "code": "INVALID_TOKEN"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not token_obj.is_valid():
        return Response(
            {"error": "Token has expired or already been used.", "code": "TOKEN_EXPIRED"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token_obj.user.is_email_verified = True
    token_obj.user.save(update_fields=["is_email_verified"])
    token_obj.is_used = True
    token_obj.save(update_fields=["is_used"])

    return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)


@extend_schema(tags=["Authentication"])
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def password_reset_request_view(request):
    """Send password reset email."""
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"].lower()

    # Always return 200 to prevent user enumeration
    try:
        user = User.objects.get(email=email)
        # Invalidate old tokens
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        reset_token = PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token.token}"
        send_mail(
            subject="Reset your ExpenseFlow password",
            message=f"Hi {user.first_name},\n\nReset your password: {reset_url}\n\nThis link expires in 1 hour.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except User.DoesNotExist:
        pass  # Silent — don't reveal whether email exists

    return Response(
        {"message": "If an account exists with that email, a reset link has been sent."},
        status=status.HTTP_200_OK,
    )


@extend_schema(tags=["Authentication"])
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """Confirm password reset using token."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    reset_token = serializer.validated_data["reset_token"]
    user = reset_token.user
    user.set_password(serializer.validated_data["new_password"])
    user.save(update_fields=["password"])

    reset_token.is_used = True
    reset_token.save(update_fields=["is_used"])

    return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)


@extend_schema(tags=["Authentication"])
class MeView(generics.RetrieveUpdateAPIView):
    """Get or update current user profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["Authentication"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Change password (requires old password verification)."""
    serializer = PasswordChangeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    if not user.check_password(serializer.validated_data["old_password"]):
        return Response(
            {"error": "Old password is incorrect.", "code": "WRONG_PASSWORD"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(serializer.validated_data["new_password"])
    user.save(update_fields=["password"])

    return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
