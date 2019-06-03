from rest_framework.permissions import BasePermission, IsAuthenticated, DjangoModelPermissions

from oscarapi.basket.operations import request_allows_access_to


class HasUser(BasePermission):
    "Only anonymous and authenticated users can access this resource."
    def has_permission(self, request, view):
        return request.user


class IsAdminUserOrRequestAllowsAccessTo(BasePermission):
    """
    Permission class that checks if a request allows access to a basket.
    """
    def has_object_permission(self, request, view, obj):
        return request_allows_access_to(request, obj) or request.user.is_staff


class IsOwner(IsAuthenticated):
    """
    Permission that checks if this object has a foreign key pointing to the
    authenticated user of this request
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class APIAdminPermission(DjangoModelPermissions):
    """
    The permission for all the admin api views, by default you get api
    access if you've got django admin access.
    
    Feel free to customize!
    """
