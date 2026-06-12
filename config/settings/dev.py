from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "*"]

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

LOGGING["root"]["level"] = "DEBUG"

try:
    import django_extensions  # noqa
    INSTALLED_APPS += ["django_extensions"]
except ImportError:
    pass
