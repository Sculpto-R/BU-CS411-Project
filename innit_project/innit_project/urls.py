from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    path('api/', include('accounts.api.urls')),
    path("admin/", admin.site.urls),
    path('landing/', account_views.landing_page, name='landing'),
    path('', account_views.home_screen, name='home'),
    path('home/', account_views.home_screen, name='home'),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('events/', include('events.urls')),
]

urlpatterns += staticfiles_urlpatterns()
