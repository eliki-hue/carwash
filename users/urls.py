from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import LoginView, UserViewSet, LogoutView

#  Router for ViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

#  Combine both
urlpatterns = [
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    
]

urlpatterns += router.urls