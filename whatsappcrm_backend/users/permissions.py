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
    Allows access only to authenticated retailers (company accounts).
    Retailers can only manage branches.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'retailer_profile')


class IsRetailerBranch(permissions.BasePermission):
    """
    Allows access only to authenticated retailer branch accounts.
    Branch accounts perform check-in/checkout operations.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'retailer_branch_profile')


class IsRetailerOrBranch(permissions.BasePermission):
    """
    Allows access to either retailer accounts or branch accounts.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (hasattr(request.user, 'retailer_profile') or 
                hasattr(request.user, 'retailer_branch_profile'))


class IsRetailerOrAdmin(permissions.BasePermission):
    """
    Allows access to retailers or admin users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or hasattr(request.user, 'retailer_profile')


class IsRetailerBranchOrAdmin(permissions.BasePermission):
    """
    Allows access to retailer branches or admin users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or hasattr(request.user, 'retailer_branch_profile')
