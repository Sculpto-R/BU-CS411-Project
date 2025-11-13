from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('api/', include('api.urls')),
    path("admin/", admin.site.urls),
    path('', account_views.landing, name='landing'),
    path('home/', account_views.home, name='home'),
    path('accounts/', include('django.contrib.auth.urls')),
]

urlpatterns += staticfiles_urlpatterns()
