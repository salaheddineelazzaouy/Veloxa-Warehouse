from functools import wraps
from django.http import Http404
from django.contrib import messages
from django.shortcuts import redirect


_ROLE_HIERARCHY = {"viewer": 1, "auditor": 2, "warehouse_manager": 3, "super_admin": 4}


def role_required(*allowed_roles):
    """
    Decorator for template views.

    Usage:
        @role_required("warehouse_manager", "super_admin")
        def product_create(request):
            ...

    Or use the shorthand constants:
        WRITE_ROLES  -> warehouse_manager, super_admin
        ADMIN_ROLES  -> super_admin only
        AUDIT_ROLES  -> auditor, warehouse_manager, super_admin
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            user_rank = _ROLE_HIERARCHY.get(getattr(request.user, "role", "viewer"), 0)
            allowed_ranks = {_ROLE_HIERARCHY.get(r, 0) for r in allowed_roles}
            if user_rank < min(allowed_ranks):
                messages.error(request, "You don't have permission to do that.")
                return redirect("dashboard")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


WRITE_ROLES = ("warehouse_manager", "super_admin")
ADMIN_ROLES = ("super_admin",)
AUDIT_ROLES = ("auditor", "warehouse_manager", "super_admin")
