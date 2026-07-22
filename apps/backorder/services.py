import logging
from django.db import transaction

from .models import BackOrder

logger = logging.getLogger(__name__)


def create_backorder(product_id: int, missing_qty: int, so_ref: str, user) -> BackOrder:
    backorder = BackOrder.objects.create(
        product_id=product_id,
        qty=missing_qty,
        sales_order_ref=so_ref,
        created_by=user,
        tenant=user.tenant,
    )
    logger.info("BackOrder created product=%d qty=%d ref=%s", product_id, missing_qty, so_ref)
    return backorder


def fulfill_backorder(backorder_id: int, qty: int, user) -> BackOrder:
    from apps.tenants.utils import get_current_tenant_id
    with transaction.atomic():
        qs = BackOrder.objects.select_for_update().filter(pk=backorder_id, status__in=["open", "partially_fulfilled"])
        tenant_id = get_current_tenant_id()
        if tenant_id is not None:
            qs = qs.filter(tenant_id=tenant_id)
        bo = qs.get()
        new_fulfilled = bo.qty_fulfilled + qty
        if new_fulfilled > bo.qty:
            raise ValueError(f"Fulfillment {qty} exceeds remaining {bo.qty_remaining}")
        bo.qty_fulfilled = new_fulfilled
        if new_fulfilled >= bo.qty:
            bo.status = BackOrder.Status.CLOSED
        else:
            bo.status = BackOrder.Status.PARTIALLY_FULFILLED
        bo.save(update_fields=["qty_fulfilled", "status"])
        logger.info("BackOrder %d fulfilled qty=%d", backorder_id, qty)
    return bo
