from django.conf import settings as django_settings


def overridable(name, default):
    """
    Seems useless but this is for readability
    """
    return getattr(django_settings, name, default)
