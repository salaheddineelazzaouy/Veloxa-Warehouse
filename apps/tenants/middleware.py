from .utils import set_current_tenant


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        if request.user.is_authenticated and hasattr(request.user, "tenant") and request.user.tenant_id:
            if not request.user.is_superuser:
                tenant = request.user.tenant
        request.tenant = tenant
        set_current_tenant(tenant)
        response = self.get_response(request)
        return response
