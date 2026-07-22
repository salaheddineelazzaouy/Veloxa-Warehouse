from django.db import models
from .utils import get_current_tenant_id


class TenantAwareManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = get_current_tenant_id()
        if tenant_id is not None:
            return qs.filter(tenant_id=tenant_id)
        return qs


class TenantAwareQuerySet(models.QuerySet):
    """Use this if you need a custom QuerySet that is tenant-aware."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tenant_filter_applied = False

    def _apply_tenant(self):
        if self._tenant_filter_applied:
            return
        tenant_id = get_current_tenant_id()
        if tenant_id is not None and self.model._meta.get_field("tenant"):
            self._tenant_filter_applied = True
            return self.filter(tenant_id=tenant_id)

    def all(self):
        qs = super().all()
        tenant_id = get_current_tenant_id()
        if tenant_id is not None and hasattr(self.model, "tenant"):
            return qs.filter(tenant_id=tenant_id)
        return qs
