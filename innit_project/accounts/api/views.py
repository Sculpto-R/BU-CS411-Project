from rest_framework import viewsets, permissions
from .serializers import UserSerializer, ProfileSerializer
from django.contrib.auth.models import User
from accounts.models import Profile

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
