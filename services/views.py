from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsOwner
from .models import Service, ServicePricing
from .serializers import ServiceSerializer, ServicePricingSerializer


class ServiceViewSet(ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]


class ServicePricingViewSet(ModelViewSet):
    queryset = ServicePricing.objects.select_related("service", "vehicle_type")
    serializer_class = ServicePricingSerializer
    permission_classes = [IsAuthenticated]