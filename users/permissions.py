from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'

class IsAnalyst(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role in ['admin', 'analyst']