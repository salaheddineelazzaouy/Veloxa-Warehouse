"""Tests for warehouse services — the core of the system.

Success criterion: All stock operations are atomic, immutable, and auditable.
"""
import pytest
from django.db import transaction
from apps.warehouse.services import (
    current_stock,
    receive_purchase_order,
    fulfill_sales_order,
    adjustment,
    reconcile,
)
from apps.warehouse.models import StockMovement
from lib.exceptions import InsufficientStock, DuplicateReference, InvalidMovement


class TestInbound:
    def test_receive_po_increases_stock(self, warehouse_user, product):
        movement = receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-001", user=warehouse_user
        )
        assert movement.qty == 100
        assert movement.type == "inbound"
        assert current_stock(product.id) == 100

    def test_duplicate_po_ref_raises_error(self, warehouse_user, product):
        receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-001", user=warehouse_user
        )
        with pytest.raises(DuplicateReference):
            receive_purchase_order(
                product_id=product.id, qty=50, po_ref="PO-001", user=warehouse_user
            )

    def test_inbound_zero_qty_raises_error(self, warehouse_user, product):
        with pytest.raises(InvalidMovement):
            receive_purchase_order(
                product_id=product.id, qty=0, po_ref="PO-002", user=warehouse_user
            )

    def test_inbound_negative_qty_raises_error(self, warehouse_user, product):
        with pytest.raises(InvalidMovement):
            receive_purchase_order(
                product_id=product.id, qty=-10, po_ref="PO-003", user=warehouse_user
            )


class TestOutbound:
    def test_fulfill_so_decreases_stock(self, warehouse_user, product):
        receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-010", user=warehouse_user
        )
        result = fulfill_sales_order(
            product_id=product.id, qty=30, so_ref="SO-001", user=warehouse_user
        )
        assert result["movement"].qty == -30
        assert result["stock_after"] == 70
        assert current_stock(product.id) == 70

    def test_fulfill_insufficient_stock_raises_error(self, warehouse_user, product):
        with pytest.raises(InsufficientStock):
            fulfill_sales_order(
                product_id=product.id, qty=10, so_ref="SO-002", user=warehouse_user
            )

    def test_fulfill_exact_stock(self, warehouse_user, product):
        receive_purchase_order(
            product_id=product.id, qty=50, po_ref="PO-020", user=warehouse_user
        )
        result = fulfill_sales_order(
            product_id=product.id, qty=50, so_ref="SO-003", user=warehouse_user
        )
        assert result["stock_after"] == 0

    def test_duplicate_so_ref_raises_error(self, warehouse_user, product):
        receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-030", user=warehouse_user
        )
        fulfill_sales_order(
            product_id=product.id, qty=10, so_ref="SO-010", user=warehouse_user
        )
        with pytest.raises(DuplicateReference):
            fulfill_sales_order(
                product_id=product.id, qty=10, so_ref="SO-010", user=warehouse_user
            )


class TestAdjustment:
    def test_adjustment_increases_stock(self, warehouse_user, product):
        movement = adjustment(
            product_id=product.id, qty=+50, user=warehouse_user,
            reason="Inventory correction"
        )
        assert movement.type == "adjustment"
        assert current_stock(product.id) == 50

    def test_adjustment_decreases_stock(self, warehouse_user, product):
        receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-040", user=warehouse_user
        )
        adjustment(
            product_id=product.id, qty=-20, user=warehouse_user,
            reason="Damaged goods"
        )
        assert current_stock(product.id) == 80

    def test_adjustment_zero_raises_error(self, warehouse_user, product):
        with pytest.raises(InvalidMovement):
            adjustment(
                product_id=product.id, qty=0, user=warehouse_user,
                reason="No change"
            )


class TestImmutability:
    def test_cannot_update_movement(self, warehouse_user, product):
        movement = receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-050", user=warehouse_user
        )
        with pytest.raises(NotImplementedError):
            movement.qty = 999
            movement.save()

    def test_cannot_delete_movement(self, warehouse_user, product):
        movement = receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-060", user=warehouse_user
        )
        with pytest.raises(NotImplementedError):
            movement.delete()

    def test_correction_flow(self, warehouse_user, product):
        """Overshipped: 50 shipped instead of 40 → net -40 via correction."""
        receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-070", user=warehouse_user
        )
        fulfill_sales_order(
            product_id=product.id, qty=50, so_ref="SO-020", user=warehouse_user
        )
        adjustment(
            product_id=product.id, qty=+10, user=warehouse_user,
            reason="Overshipment correction SO-020"
        )
        assert current_stock(product.id) == 60  # 100 - 50 + 10


class TestAtomicity:
    def test_inbound_rolls_back_on_error(self, warehouse_user, product):
        receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-080", user=warehouse_user
        )
        with pytest.raises(DuplicateReference):
            receive_purchase_order(
                product_id=product.id, qty=50, po_ref="PO-080", user=warehouse_user
            )
        assert current_stock(product.id) == 100  # First PO succeeded

    def test_outbound_rolls_back_on_error(self, warehouse_user, product):
        with pytest.raises(InsufficientStock):
            with transaction.atomic():
                fulfill_sales_order(
                    product_id=product.id, qty=10,
                    so_ref="SO-030", user=warehouse_user
                )
        assert current_stock(product.id) == 0


class TestMissingProduct:
    def test_inbound_nonexistent_product_raises_notfound(self, warehouse_user):
        from django.core.exceptions import ObjectDoesNotExist
        with pytest.raises(ObjectDoesNotExist):
            receive_purchase_order(
                product_id=99999, qty=10, po_ref="PO-XXX", user=warehouse_user
            )

    def test_outbound_nonexistent_product_raises_notfound(self, warehouse_user):
        from django.core.exceptions import ObjectDoesNotExist
        with pytest.raises(ObjectDoesNotExist):
            fulfill_sales_order(
                product_id=99999, qty=10, so_ref="SO-XXX", user=warehouse_user
            )

    def test_adjustment_nonexistent_product_raises_notfound(self, warehouse_user):
        from django.core.exceptions import ObjectDoesNotExist
        with pytest.raises(ObjectDoesNotExist):
            adjustment(
                product_id=99999, qty=10, user=warehouse_user, reason="Missing"
            )


class TestReconciliation:
    def test_matched_stock(self, warehouse_user, product):
        receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-090", user=warehouse_user
        )
        result = reconcile(product.id, 100)
        assert result["status"] == "ok"
        assert result["diff"] == 0

    def test_mismatched_stock(self, warehouse_user, product):
        receive_purchase_order(
            product_id=product.id, qty=100, po_ref="PO-100", user=warehouse_user
        )
        result = reconcile(product.id, 95)
        assert result["status"] == "discrepancy"
        assert result["diff"] == -5
