from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import Profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'date_of_birth', 'age_verified', 'presets', 'custom_preferences']
