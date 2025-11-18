from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    # Landing + home
    path("", views.landing_page, name="landing"),
    path("home/", views.home_screen, name="home"),

    # Auth
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),

    # Registration steps
    path("register/step1/", views.reg_step1, name="register_step1"),
    path("register/step2/", views.reg_step2, name="register_step2"),
    path("register/step3/", views.reg_step3, name="register_step3"),
    path("register/step4/", views.reg_step4, name="register_step4"),
    path("register/welcome/", views.welcome, name="welcome"),

    # Profile
    path("profile/", views.profile, name="profile"),
]

