# users/permissions.py

from rest_framework.permissions import BasePermission


class IsManagerOrOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['manager', 'owner']