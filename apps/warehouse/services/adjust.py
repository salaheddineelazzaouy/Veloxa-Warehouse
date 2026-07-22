import logging
from uuid import uuid4
from django.db import transaction

from ..models import StockMovement, Product
from lib.exceptions import InvalidMovement

logger = logging.getLogger(__name__)


def adjustment(
    product_id: int,
    qty: int,
    user,
    reason: str,
    approved_by=None,
) -> StockMovement:
    if qty == 0:
        raise InvalidMovement("Adjustment quantity cannot be zero")

    with transaction.atomic():
        product = Product.objects.select_for_update().get(
            pk=product_id, is_active=True
        )

        movement = StockMovement.objects.create(
            product=product,
            qty=qty,
            type=StockMovement.Type.ADJUSTMENT,
            reference=f"ADJ-{uuid4().hex[:8].upper()}",
            note=f"{reason} (approved by {approved_by})" if approved_by else reason,
            created_by=user,
            tenant=user.tenant,
        )

        logger.info(
            "Adjustment product=%s qty=%+d ref=%s user=%s",
            product.sku, qty, movement.reference, user,
        )

    return movement
