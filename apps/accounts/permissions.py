from rest_framework.permissions import BasePermission


def setup_groups():
    pass


def _role_rank(user):
    ranks = {"viewer": 1, "auditor": 2, "warehouse_manager": 3, "super_admin": 4}
    return ranks.get(getattr(user, "role", "viewer"), 1)


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.role == "super_admin")
        )


class IsWarehouseManager(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("super_admin", "warehouse_manager")
        )


class IsAuditor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("super_admin", "warehouse_manager", "auditor")
        )


class RoleBasedPermission(BasePermission):
    """
    Assign per-action role requirements.

    On the view, set:
        role_map = {
            "list": "viewer",
            "retrieve": "viewer",
            "create": "warehouse_manager",
            "update": "warehouse_manager",
            "partial_update": "warehouse_manager",
            "destroy": "super_admin",
        }

    Or use the defaults (warehouse_manager for write, viewer for read).
    """

    _ROLE_HIERARCHY = {"viewer": 1, "auditor": 2, "warehouse_manager": 3, "super_admin": 4}

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        action = getattr(view, "action", None)
        if action is None:
            action = request.method.lower()

        role_map = getattr(view, "role_map", None)
        if role_map and action in role_map:
            required_role = role_map[action]
        else:
            if request.method in ("GET", "HEAD", "OPTIONS"):
                required_role = "viewer"
            else:
                required_role = "warehouse_manager"

        return self._ROLE_HIERARCHY.get(request.user.role, 0) >= self._ROLE_HIERARCHY.get(required_role, 99)
