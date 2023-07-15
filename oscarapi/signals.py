import django
from django.dispatch import Signal


oscarapi_post_checkout_args = ["order", "user", "request", "response"]

if django.VERSION >= (3, 0):
    oscarapi_post_checkout = Signal()
else:
    oscarapi_post_checkout = Signal(providing_args=oscarapi_post_checkout_args)
