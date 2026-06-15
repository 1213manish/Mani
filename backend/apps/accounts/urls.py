from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    logout_view,
    verify_email_view,
    password_reset_request_view,
    password_reset_confirm_view,
    MeView,
    change_password_view,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", logout_view, name="auth-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("verify-email/<uuid:token>/", verify_email_view, name="auth-verify-email"),
    path("password-reset/", password_reset_request_view, name="auth-password-reset"),
    path("password-reset/confirm/", password_reset_confirm_view, name="auth-password-reset-confirm"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("change-password/", change_password_view, name="auth-change-password"),
]
