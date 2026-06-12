import logging
from django.db.models import Sum

logger = logging.getLogger(__name__)


def current_stock(product_id: int) -> int:
    from ..models import StockMovement
    result = StockMovement.objects.filter(product_id=product_id).aggregate(
        total=Sum("qty")
    )
    return result["total"] or 0
