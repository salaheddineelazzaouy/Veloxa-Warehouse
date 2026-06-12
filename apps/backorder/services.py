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
    )
    logger.info("BackOrder created product=%d qty=%d ref=%s", product_id, missing_qty, so_ref)
    return backorder


def fulfill_backorder(backorder_id: int, qty: int, user) -> BackOrder:
    with transaction.atomic():
        bo = BackOrder.objects.select_for_update().get(pk=backorder_id, status__in=["open", "partially_fulfilled"])
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
