from rest_framework import serializers
from .models import Map, Variable

class VariableSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = Variable
        fields = ['name', 'data_type', 'value']

    def get_value(self, obj):
        return obj.cast_value()

class MapSerializer(serializers.ModelSerializer):
    variables = VariableSerializer(many=True)

    class Meta:
        model = Map
        fields = ['name', 'variables']
