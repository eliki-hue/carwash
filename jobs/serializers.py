from rest_framework import serializers
from .models import Job
from services.models import ServicePricing


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = "__all__"
        read_only_fields = ["price", "status"]

    def create(self, validated_data):
        service = validated_data["service"]
        vehicle_type = validated_data["vehicle_type"]

        try:
            pricing = ServicePricing.objects.get(
                service=service,
                vehicle_type=vehicle_type
            )
        except ServicePricing.DoesNotExist:
            raise serializers.ValidationError(
                "No pricing set for this service and vehicle type"
            )

        validated_data["price"] = pricing.price
        validated_data["status"] = "pending"

        return super().create(validated_data)