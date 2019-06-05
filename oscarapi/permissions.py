from rest_framework.permissions import (
    BasePermission,
    IsAdminUser,
    IsAuthenticated,
    DjangoModelPermissions,
)

from oscarapi.basket.operations import request_allows_access_to


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
    The permission for all the admin api views. You only get admin api access if you
    are a staff user. You will get access to the objects according to the model
    persmissons you have (iew / add / change / delete)

    Feel free to customize!
    """

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }

    def has_permission(self, request, view):
        if not request.user.is_staff:
            return False
        return super(APIAdminPermission, self).has_permission(request, view)
