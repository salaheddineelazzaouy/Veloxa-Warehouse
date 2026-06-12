import logging

from .stock import current_stock

logger = logging.getLogger(__name__)


def reconcile(product_id: int, physical_count: int) -> dict:
    system_stock = current_stock(product_id)
    diff = physical_count - system_stock

    result = {
        "product_id": product_id,
        "system": system_stock,
        "physical": physical_count,
        "diff": diff,
    }

    if diff == 0:
        result["status"] = "ok"
    else:
        result["status"] = "discrepancy"
        logger.warning(
            "Reconciliation product=%d system=%d physical=%d diff=%+d",
            product_id, system_stock, physical_count, diff,
        )

    return result
