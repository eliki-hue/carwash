from django.db.models import Q

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .permissions import IsOwner
from .serializers import (
    LoginSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


# -------------------------------------------------------
# LOGIN
# -------------------------------------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": user.role,
                "user_id": user.id,
                "username": user.username,
            }
        )


# -------------------------------------------------------
# USERS
# -------------------------------------------------------
class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("-id")

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "activate",
            "reset_password",
        ]:
            return [IsAuthenticated(), IsOwner()]

        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer

        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer

        return UserSerializer

    def get_queryset(self):
        queryset = (
            User.objects.all()
            .only(
                "id",
                "username",
                "first_name",
                "last_name",
                "email",
                "role",
                "is_active",
                "date_joined",
            )
            .order_by("-id")
        )

        # ---------------------------------
        # Search
        # ---------------------------------
        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
            )

        # ---------------------------------
        # Role filter
        # ---------------------------------
        role = self.request.query_params.get("role")

        if role:
            queryset = queryset.filter(role=role)

        # ---------------------------------
        # Active filter
        # ---------------------------------
        active = self.request.query_params.get("active")

        if active is not None:
            queryset = queryset.filter(
                is_active=active.lower() == "true"
            )

        return queryset

    # ---------------------------------------------------
    # SOFT DELETE
    # ---------------------------------------------------
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        if user == request.user:
            return Response(
                {
                    "error": "You cannot deactivate your own account."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = False
        user.save(update_fields=["is_active"])

        return Response(
            {
                "message": "User deactivated successfully."
            }
        )

    # ---------------------------------------------------
    # ACTIVATE USER
    # ---------------------------------------------------
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        user = self.get_object()

        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response(
            {
                "message": "User activated successfully."
            }
        )

    # ---------------------------------------------------
    # RESET PASSWORD
    # ---------------------------------------------------
    @action(detail=True, methods=["post"])
    def reset_password(self, request, pk=None):
        user = self.get_object()

        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not password:
            return Response(
                {
                    "error": "Password is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if password != confirm_password:
            return Response(
                {
                    "error": "Passwords do not match."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save()

        return Response(
            {
                "message": "Password reset successfully."
            }
        )


# -------------------------------------------------------
# LOGOUT
# -------------------------------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {
                    "error": "Refresh token required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {
                    "message": "Logged out successfully."
                }
            )

        except Exception as e:
            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )