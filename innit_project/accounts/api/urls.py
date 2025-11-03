from rest_framework import routers
from accounts.api.views import UserViewSet, ProfileViewSet
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', ProfileViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
