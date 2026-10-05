"""URL patterns for the accounts application."""
from django.urls import path
from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("verify-email/<str:token>/", views.verify_email_view, name="verify_email"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("reset-password/<str:token>/", views.reset_password_view, name="reset_password"),
    path("change-password/", views.change_password_view, name="change_password"),
]
