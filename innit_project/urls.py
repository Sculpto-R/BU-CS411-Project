from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    # Landing page
    path('', account_views.landing_page, name='landing'),

    # Admin panel
    path('admin/', admin.site.urls),

    # Accounts (your account system)
    path('accounts/', include('accounts.urls')),              # your custom URLs
    path('accounts/', include('django.contrib.auth.urls')),   # login/logout/password reset

    # Home screen after login
    path('home/', account_views.home_screen, name='home'),

    # API
    path('api/', include('api.urls')),

    # Event map
    path('events/', include('events.urls')),
]

urlpatterns += staticfiles_urlpatterns()
