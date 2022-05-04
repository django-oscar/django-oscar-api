default_app_config = "oscarapi.apps.OscarAPIConfig"

try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata as importlib_metadata

version = importlib_metadata.version("django-oscar-api")
