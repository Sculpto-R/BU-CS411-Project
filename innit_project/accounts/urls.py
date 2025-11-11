from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'accounts'

urlpatterns = [
    path('', views.profile, name='profile'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Multi-step registration
    path('register/step-1/', views.reg_step1, name='register_step1'),
    path('register/step-2/', views.reg_step2, name='register_step2'),
    path('register/step-3/', views.reg_step3, name='register_step3'),
    path('register/step-4/', views.reg_step4, name='register_step4'),
    path('register/welcome/', views.welcome, name='welcome'),

    # Account settings editing
    path('edit/account/', views.edit_account, name='edit_account'),
    path('edit/dob/', views.edit_dob, name='edit_dob'),
    path('edit/preferences/', views.edit_preferences, name='edit_preferences'),
    path('password_change/', views.password_change, name='password_change'),

    # Mapping + Home
    path('api/events/', views.api_find_events, name='api_find_events'),
    path('home/', views.home_screen, name='home'),
]
