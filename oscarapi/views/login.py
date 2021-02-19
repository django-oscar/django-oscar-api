from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from oscar.apps.customer.signals import user_registered
from oscar.core.loading import get_class, get_model

from oscarapi.utils.session import login_and_upgrade_session
from oscarapi.utils.loading import get_api_classes
from oscarapi.basket import operations


LoginSerializer, UserSerializer, RegisterUserSerializer = get_api_classes(
    "serializers.login", ["LoginSerializer", "UserSerializer", "RegisterUserSerializer"]
)
RegisterUserMixin = get_class("customer.mixins", "RegisterUserMixin")

Basket = get_model("basket", "Basket")
User = get_user_model()

__all__ = ("LoginView", "UserDetail")


class LoginView(APIView):
    """
    Api for logging in users.

    DELETE:
    Log the user out by destroying the session.
    Anonymous users will have their cart destroyed as well, because there is
    no way to reach it anymore

    POST(username, password):
    1. The user will be authenticated. The next steps will only be
       performed is login is successful. Logging in logged in users results in
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

    GET:
    Get the details of the logged in user. Can be enabled/disabled with the
    OSCARAPI_EXPOSE_USER_DETAILS setting. If more details are needed,
    use the ``OSCARAPI_USER_FIELDS`` setting to change the fields the
    ``UserSerializer`` will render.
    """

    serializer_class = LoginSerializer

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if getattr(settings, "OSCARAPI_EXPOSE_USER_DETAILS", False):
                ser = UserSerializer(request.user, many=False)
                return Response(ser.data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise MethodNotAllowed("GET")

    def merge_baskets(self, anonymous_basket, basket):
        "Hook to enforce rules when merging baskets."
        basket.merge(anonymous_basket)

    def post(self, request, *args, **kwargs):
        ser = self.serializer_class(data=request.data)
        if ser.is_valid():

            anonymous_basket = operations.get_anonymous_basket(request)

            user = ser.instance

            # refuse to login logged in users, to avoid attaching sessions to
            # multiple users at the same time.
            if request.user.is_authenticated:
                return Response(
                    {"detail": "Session is in use, log out first"},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED,
                )

            request.user = user

            login_and_upgrade_session(request._request, user)

            # merge anonymous basket with authenticated basket.
            basket = operations.get_user_basket(user)
            if anonymous_basket is not None:
                self.merge_baskets(anonymous_basket, basket)

            operations.store_basket_in_session(basket, request.session)

            return Response("")

        return Response(ser.errors, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, *args, **kwargs):
        """
        Destroy the session.

        for anonymous users that means having their basket destroyed as well,
        because there is no way to reach it otherwise.
        """
        request = request._request
        if request.user.is_anonymous:
            basket = operations.get_anonymous_basket(request)
            if basket:
                operations.flush_and_delete_basket(basket)

        request.session.clear()
        request.session.delete()
        request.session = None

        return Response("")


class UserDetail(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    def get(self, request, *args, **kwargs):
        if getattr(settings, "OSCARAPI_EXPOSE_USER_DETAILS", False):
            return super().get(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegistrationView(APIView, RegisterUserMixin):
    """
    API for registering users

    POST(email, password1, password2):
    {
        "email": "user@my-domain.com",
        "password1": "MyVerySecretPassword123"
        "password2": "MyVerySecretPassword123"
    }

    Will create a new user when the user with the specific email does
    not exist (HTTP_201_CREATED). It will also send a user_registered signal.

    It won't login the newly created user, You can do this with the login API.
    """

    serializer_class = RegisterUserSerializer

    def post(self, request, *args, **kwargs):
        if not getattr(settings, "OSCARAPI_ENABLE_REGISTRATION", False):
            return Response("Unauthorized", status=status.HTTP_401_UNAUTHORIZED)

        ser = self.serializer_class(data=request.data)

        if ser.is_valid():
            # create the user
            user = ser.save()

            if getattr(settings, "OSCAR_SEND_REGISTRATION_EMAIL", False):
                self.send_registration_email(user)
            # send the same signal as oscar is sending
            user_registered.send(sender=self, request=request, user=user)

            return Response(user.email, status=status.HTTP_201_CREATED)

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
