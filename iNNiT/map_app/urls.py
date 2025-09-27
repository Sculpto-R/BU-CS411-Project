from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MapViewSet

router = DefaultRouter()
router.register(r'maps', MapViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
