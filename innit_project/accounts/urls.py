from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.profile, name='profile'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # Multi-step registration
    path('register/step-1/', views.reg_step1, name='register_step1'),
    path('register/step-2/', views.reg_step2, name='register_step2'),
    path('register/step-3/', views.reg_step3, name='register_step3'),
    path('register/step-4/', views.reg_step4, name='register_step4'),
    path('register/welcome/', views.welcome, name='welcome'),
]
