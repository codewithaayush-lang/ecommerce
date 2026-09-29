"""URL routing for authentication. Mounted under /api/auth/."""

from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("csrf/", views.csrf, name="csrf"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("me/", views.me, name="me"),
]
