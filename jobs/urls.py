from rest_framework.routers import DefaultRouter
from .views import JobViewSet

router = DefaultRouter()
router.register('jobs', JobViewSet, basename='jobs')

urlpatterns = router.urls