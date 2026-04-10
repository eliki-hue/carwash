from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, ServicePricingViewSet

router = DefaultRouter()
router.register(r'services', ServiceViewSet)
router.register(r'pricing', ServicePricingViewSet)

urlpatterns = router.urls