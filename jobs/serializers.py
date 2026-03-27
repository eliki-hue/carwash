# jobs/serializers.py

from rest_framework import serializers
from .models import Job


class JobSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    staff_name = serializers.CharField(source='assigned_staff.username', read_only=True)

    class Meta:
        model = Job
        fields = [
            'id',
            'plate_number',
            'car_type',
            'service',
            'service_name',
            'assigned_staff',
            'staff_name',
            'status',
            'price',
            'start_time',
            'end_time',
            'created_at',
        ]