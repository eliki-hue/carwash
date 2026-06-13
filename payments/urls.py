from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    PaymentViewSet,
    mpesa_callback,
)

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payments')

urlpatterns = [
    path(
        'payments/mpesa-callback/',
        mpesa_callback,
        name='mpesa-callback'
    ),
]

urlpatterns += router.urls