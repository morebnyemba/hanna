# whatsappcrm_backend/users/permissions.py
"""
Custom permission classes for user-related access control.
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsRetailer(permissions.BasePermission):
    """
    Allows access only to authenticated retailers.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'retailer_profile')


class IsRetailerOrAdmin(permissions.BasePermission):
    """
    Allows access to retailers or admin users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or hasattr(request.user, 'retailer_profile')
