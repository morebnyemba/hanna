from rest_framework import permissions

class IsManufacturer(permissions.BasePermission):
    """
    Custom permission to only allow manufacturers to access a view.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'manufacturer_profile')
