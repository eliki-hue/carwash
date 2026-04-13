from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, ServicePricingViewSet

router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='services')
router.register(r'pricing', ServicePricingViewSet, basename='pricing')

urlpatterns = router.urls