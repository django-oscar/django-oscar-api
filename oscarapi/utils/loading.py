from django.conf import settings
from oscar.core.loading import (
    _pluck_classes,
    _import_module,
)

OSCARAPI_OVERRIDE_MODULE = getattr(settings, "OSCARAPI_OVERRIDE_MODULE", None)


def oscarapi_class_loader(module_label, classnames, module_prefix="oscarapi"):
    """Oscarapi uses a bit simpler method of overrides"""
    default_module_name = "%s.%s" % (module_prefix, module_label)
    default_module = _import_module(default_module_name, classnames)
    if OSCARAPI_OVERRIDE_MODULE is None:
        return _pluck_classes([default_module], classnames)
    else:
        override_module_name = "%s.%s" % (OSCARAPI_OVERRIDE_MODULE, module_label)
        override_module = _import_module(override_module_name, classnames)
        return _pluck_classes([override_module, default_module], classnames)


def get_api_classes(module_label, classnames):
    return oscarapi_class_loader(module_label, classnames, "oscarapi")


def get_api_class(module_label, classname):
    return get_api_classes(module_label, [classname])[0]
