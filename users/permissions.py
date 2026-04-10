from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "owner"


class IsManagerOrOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["owner", "manager"]


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "staff"