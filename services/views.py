from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .models import Service
from .serializers import ServiceSerializer


from users.permissions import IsManagerOrOwner

class ServiceViewSet(ModelViewSet):
    queryset = Service.objects.all().order_by('price')
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsManagerOrOwner()]
        return [IsAuthenticated()]