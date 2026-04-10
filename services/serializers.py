from rest_framework import serializers
from .models import Service, ServicePricing


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class ServicePricingSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    vehicle_name = serializers.CharField(source="vehicle_type.name", read_only=True)

    class Meta:
        model = ServicePricing
        fields = [
            "id",
            "service",
            "service_name",
            "vehicle_type",
            "vehicle_name",
            "price",
        ]

    def validate(self, data):
        service = data.get("service")
        vehicle = data.get("vehicle_type")

        if ServicePricing.objects.filter(service=service, vehicle_type=vehicle).exists():
            raise serializers.ValidationError(
                "Pricing for this service and vehicle already exists"
            )

        return data