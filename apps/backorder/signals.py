import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.warehouse.models import StockMovement
from .services import create_backorder
from apps.warehouse.services.stock import current_stock

logger = logging.getLogger(__name__)


@receiver(post_save, sender=StockMovement)
def handle_outbound_backorder(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.type != StockMovement.Type.OUTBOUND:
        return

    stock = current_stock(instance.product_id)
    if stock >= 0:
        return

    requested_qty = abs(instance.qty)
    stock_before = stock + requested_qty
    missing = max(0, requested_qty - stock_before)

    if missing > 0:
        create_backorder(
            product_id=instance.product_id,
            missing_qty=missing,
            so_ref=instance.reference,
            user=instance.created_by,
        )
