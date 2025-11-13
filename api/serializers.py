from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        # safest while we're iterating – exposes everything your Event model has
        fields = "__all__"
