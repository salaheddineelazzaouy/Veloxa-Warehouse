"""Tests for backorder services — isolated deficit tracking."""
import pytest
from apps.backorder.services import create_backorder, fulfill_backorder


class TestBackOrder:
    def test_create_backorder(self, warehouse_user, product):
        bo = create_backorder(
            product_id=product.id,
            missing_qty=10,
            so_ref="SO-100",
            user=warehouse_user,
        )
        assert bo.qty == 10
        assert bo.status == "open"
        assert bo.qty_remaining == 10

    def test_fulfill_backorder(self, warehouse_user, product):
        bo = create_backorder(
            product_id=product.id, missing_qty=10,
            so_ref="SO-101", user=warehouse_user,
        )
        fulfill_backorder(bo.id, 10, warehouse_user)
        bo.refresh_from_db()
        assert bo.status == "closed"
        assert bo.qty_fulfilled == 10

    def test_partial_fulfill(self, warehouse_user, product):
        bo = create_backorder(
            product_id=product.id, missing_qty=10,
            so_ref="SO-102", user=warehouse_user,
        )
        fulfill_backorder(bo.id, 4, warehouse_user)
        bo.refresh_from_db()
        assert bo.status == "partially_fulfilled"
        assert bo.qty_fulfilled == 4
        assert bo.qty_remaining == 6

    def test_fulfill_excess_raises_error(self, warehouse_user, product):
        bo = create_backorder(
            product_id=product.id, missing_qty=5,
            so_ref="SO-103", user=warehouse_user,
        )
        with pytest.raises(ValueError):
            fulfill_backorder(bo.id, 10, warehouse_user)
