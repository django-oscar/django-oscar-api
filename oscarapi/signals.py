from django.dispatch import Signal

oscarapi_post_checkout = Signal(providing_args=["order", "user", "request", "response"])
