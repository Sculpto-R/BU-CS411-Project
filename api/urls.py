from django.urls import path
from . import views

urlpatterns = [
    path("classify/preview/", views.classify_preview, name="classify_preview"),

]