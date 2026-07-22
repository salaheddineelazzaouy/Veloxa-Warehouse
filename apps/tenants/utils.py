import threading

_thread_local = threading.local()


def set_current_tenant(tenant):
    _thread_local.tenant = tenant


def get_current_tenant():
    return getattr(_thread_local, "tenant", None)


def get_current_tenant_id():
    tenant = get_current_tenant()
    return tenant.id if tenant else None
