from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Landing (public)
    path('', account_views.landing_page, name='landing'),

    # Home (authenticated)
    path('home/', account_views.home_screen, name='home'),

    # Accounts app (login/register/profile)
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # other.
]
