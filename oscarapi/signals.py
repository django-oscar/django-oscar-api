import django
from django.dispatch import Signal


oscarapi_post_checkout_args = ["order", "user", "request", "response"]

oscarapi_post_checkout = Signal()
