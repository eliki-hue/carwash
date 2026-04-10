from rest_framework.routers import DefaultRouter
from .views import VehicleTypeViewSet

router = DefaultRouter()
router.register(r'vehicles', VehicleTypeViewSet)

urlpatterns = router.urls