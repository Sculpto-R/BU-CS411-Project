from django.shortcuts import render

from rest_framework import viewsets
from .models import Map
from .serializers import MapSerializer


class MapViewSet(viewsets.ModelViewSet):
    queryset = Map.objects.all()
    serializer_class = MapSerializer
