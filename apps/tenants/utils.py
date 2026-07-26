import logging
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_thread_local = threading.local()

_TENANT_BYPASS = "_tenant_bypass"


def set_current_tenant(tenant):
    _thread_local.tenant = tenant


def get_current_tenant():
    return getattr(_thread_local, "tenant", None)


def get_current_tenant_id():
    tenant = get_current_tenant()
    return tenant.id if tenant else None


def is_tenant_bypassed():
    return getattr(_thread_local, _TENANT_BYPASS, False)


@contextmanager
def tenant_context(tenant=None, bypass=False):
    """Set tenant context for the current thread.

    Usage:
        # Set a specific tenant for the duration of the block
        with tenant_context(tenant=my_tenant):
            qs = Product.objects.all()  # filtered by my_tenant

        # Bypass tenant filtering entirely (for superuser/management commands)
        with tenant_context(bypass=True):
            qs = Product.objects.all()  # unfiltered, but explicitly opted-in
    """
    prev_tenant = getattr(_thread_local, "tenant", None)
    prev_bypass = getattr(_thread_local, _TENANT_BYPASS, False)

    _thread_local.tenant = tenant
    _thread_local._tenant_bypass = bypass

    try:
        yield
    finally:
        _thread_local.tenant = prev_tenant
        _thread_local._tenant_bypass = prev_bypass


def bypass_tenant():
    """Convenience context manager: bypass tenant filtering entirely."""
    return tenant_context(bypass=True)
