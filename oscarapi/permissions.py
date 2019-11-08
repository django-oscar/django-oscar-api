from django.conf import settings

from rest_framework.permissions import (
    BasePermission,
    IsAuthenticated,
    DjangoModelPermissions,
)

from oscarapi.basket.operations import request_allows_access_to


class IsOwner(IsAuthenticated):
    """
    Permission that checks if this object has a foreign key pointing to the
    authenticated user of this request
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class APIAdminPermission(DjangoModelPermissions):
    """
    The permission for all the admin api views. You only get admin api access when:
    - OSCARAPI_BLOCK_ADMIN_API_ACCESS is false
    - you are a staff user (is_staff)
    - you have any of the model permissions needed (view / add / change / delete)

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

    @staticmethod
    def disallowed_by_setting_and_request(request):
        return (
            getattr(settings, "OSCARAPI_BLOCK_ADMIN_API_ACCESS", True)
            or not request.user.is_staff
        )

    def has_permission(self, request, view):
        if self.disallowed_by_setting_and_request(request):
            return False
        return super(APIAdminPermission, self).has_permission(request, view)


class RequestAllowsAccessTo(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request_allows_access_to(request, obj)
