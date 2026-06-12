import logging
from .models import AuditLog

logger = logging.getLogger(__name__)


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.user.is_authenticated:
            if not request.path.startswith("/admin/"):
                try:
                    AuditLog.objects.create(
                        user=request.user,
                        action={
                            "POST": "create",
                            "PUT": "update",
                            "PATCH": "update",
                            "DELETE": "delete",
                        }.get(request.method, "update"),
                        table_name="api_request",
                        changes={"path": request.path, "method": request.method},
                        ip_address=request.META.get("REMOTE_ADDR"),
                        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
                    )
                except Exception:
                    logger.exception("Failed to log audit entry")
        return response
