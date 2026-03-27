# jobs/serializers.py

from rest_framework import serializers
from .models import Job


class JobSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    staff_name = serializers.CharField(source='assigned_staff.username', read_only=True)

    class Meta:
        model = Job
        fields = '__all__'

    def create(self, validated_data):
        service = validated_data['service']
        validated_data['price'] = service.price
        return super().create(validated_data)