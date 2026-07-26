import logging
from django.db import models
from .utils import get_current_tenant_id, is_tenant_bypassed

logger = logging.getLogger(__name__)


class TenantAwareManager(models.Manager):
    """Filters querysets by the current thread's tenant.

    Behavior:
    - If a tenant is set → filter by tenant_id
    - If bypass is active → return unfiltered (explicit opt-in)
    - If neither → raise ImproperlyConfigured to prevent cross-tenant leakage
    """

    def get_queryset(self):
        qs = super().get_queryset()
        if is_tenant_bypassed():
            return qs
        tenant_id = get_current_tenant_id()
        if tenant_id is not None:
            return qs.filter(tenant_id=tenant_id)
        # No tenant set and no bypass — this is a bug, not a feature.
        # Raise to prevent silent cross-tenant data leakage.
        raise RuntimeError(
            f"{self.model.__name__}.objects used without tenant context. "
            "Wrap your code in `with tenant_context(tenant):` or "
            "`with tenant_context(bypass=True):` if cross-tenant access is intentional."
        )


class TenantAwareQuerySet(models.QuerySet):
    """Use this if you need a custom QuerySet that is tenant-aware."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tenant_filter_applied = False

    def _apply_tenant(self):
        if self._tenant_filter_applied:
            return
        if is_tenant_bypassed():
            self._tenant_filter_applied = True
            return
        tenant_id = get_current_tenant_id()
        if tenant_id is not None and self.model._meta.get_field("tenant"):
            self._tenant_filter_applied = True
            return self.filter(tenant_id=tenant_id)

    def all(self):
        qs = super().all()
        if is_tenant_bypassed():
            return qs
        tenant_id = get_current_tenant_id()
        if tenant_id is not None and hasattr(self.model, "tenant"):
            return qs.filter(tenant_id=tenant_id)
        raise RuntimeError(
            f"{self.model.__name__} QuerySet used without tenant context. "
            "Wrap your code in `with tenant_context(tenant):` or "
            "`with tenant_context(bypass=True):` if cross-tenant access is intentional."
        )
