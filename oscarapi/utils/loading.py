from django.conf import settings
from oscar.core.loading import _pluck_classes, _import_module

OSCARAPI_OVERRIDE_MODULES = getattr(settings, "OSCARAPI_OVERRIDE_MODULES", [])


def oscarapi_class_loader(module_label, classnames, module_prefix="oscarapi"):
    """Oscarapi uses a bit simpler method of overrides"""
    default_module_name = "%s.%s" % (module_prefix, module_label)
    default_module = _import_module(default_module_name, classnames)
    class_search_modules = []

    # load all modules to search for classes in
    for module_name in OSCARAPI_OVERRIDE_MODULES:  # could be empty
        override_module_name = "%s.%s" % (module_name, module_label)
        override_module = _import_module(override_module_name, classnames)
        if override_module is not None:
            class_search_modules.append(override_module)

    # add the module from the standard oscarapi package
    class_search_modules.append(default_module)
    return _pluck_classes(class_search_modules, classnames)


def get_api_classes(module_label, classnames):
    return oscarapi_class_loader(module_label, classnames, "oscarapi")


def get_api_class(module_label, classname):
    return get_api_classes(module_label, [classname])[0]
