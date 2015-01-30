from rest_framework.permissions import BasePermission


class IsAdminUserOrRequestOwner(BasePermission):
    """
    Permission that checks if this object belongg to this request.

    A method called ``request_owner(request)`` will be called on the object::

        obj.request_owner(request_owner)
    """

    def has_permission(self, request, view):
        return request.user

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'request_owner'):
            return obj.request_owner(request) or request.user.is_staff

        return False
