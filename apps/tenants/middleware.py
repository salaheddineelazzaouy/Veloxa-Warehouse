from .utils import set_current_tenant, _thread_local


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        bypass = False

        if not request.user.is_authenticated or request.user.is_superuser:
            bypass = True
        elif hasattr(request.user, "tenant") and request.user.tenant_id:
            tenant = request.user.tenant

        if tenant is None:
            bypass = True

        request.tenant = tenant
        set_current_tenant(tenant)
        _thread_local._tenant_bypass = bypass

        response = self.get_response(request)
        return response
