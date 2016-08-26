from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import APIView

from oscarapi import serializers
from oscarapi.utils import login_and_upgrade_session
from oscarapi.basket import operations
from oscar.core.loading import get_model


__all__ = ('LoginView',)

Basket = get_model('basket', 'Basket')


class LoginView(APIView):
    """
    Api for logging in users.

    DELETE:
    Log the user out by destroying the session.
    Anonymous users will have their cart destroyed as well, because there is
    no way to reach it anymoore

    POST(username, password):
    1. The user will be authenticated. The next steps will only be
       performed is login is succesful. Logging in logged in users results in
       405.
    2. The anonymous cart will be merged with the private cart associated with
       that authenticated user.
    3. A new session will be started, this session identifies the authenticated
       user for the duration of the session, without further need for
       authentication.
    4. The new, merged cart will be associated with this session.
    5. The anonymous session will be terminated.
    6. A response will be issued containing the new session id as a header
       (only when the request contained the session header as well).

    GET (enabled in DEBUG mode only):
    Get the details of the logged in user.
    If more details are needed, use the ``OSCARAPI_USER_FIELDS`` setting to change
    the fields the ``UserSerializer`` will render.
    """
    serializer_class = serializers.LoginSerializer

    def get(self, request, format=None):
        if settings.DEBUG:
            if request.user.is_authenticated():
                ser = serializers.UserSerializer(request.user, many=False)
                return Response(ser.data)
            return Response(status=status.HTTP_204_NO_CONTENT)

        raise MethodNotAllowed('GET')

    def merge_baskets(self, anonymous_basket, basket):
        "Hook to enforce rules when merging baskets."
        basket.merge(anonymous_basket)
        anonymous_basket.delete()

    def post(self, request, format=None):
        ser = self.serializer_class(data=request.data)
        if ser.is_valid():

            anonymous_basket = operations.get_anonymous_basket(request)

            user = ser.instance

            # refuse to login logged in users, to avoid attaching sessions to
            # multiple users at the same time.
            if request.user.is_authenticated():
                return Response(
                    {'detail': 'Session is in use, log out first'},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED)

            request.user = user

            login_and_upgrade_session(request._request, user)

            # merge anonymous basket with authenticated basket.
            basket = operations.get_user_basket(user)
            if anonymous_basket is not None:
                self.merge_baskets(anonymous_basket, basket)

            operations.store_basket_in_session(basket, request.session)

            return Response()

        return Response(ser.errors, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, format=None):
        """
        Destroy the session.

        for anonymous users that means having their basket destroyed as well,
        because there is no way to reach it otherwise.
        """
        request = request._request
        if request.user.is_anonymous():
            basket = operations.get_anonymous_basket(request)
            if basket:
                operations.flush_and_delete_basket(basket)

        request.session.clear()
        request.session.delete()
        request.session = None

        return Response()
