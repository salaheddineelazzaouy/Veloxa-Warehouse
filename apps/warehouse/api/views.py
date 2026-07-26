import logging
from rest_framework import generics, status
from rest_framework.response import Response

from django.db.models import Sum, Count, Q, Subquery, OuterRef, IntegerField
from django.utils import timezone
from datetime import timedelta

from ..models import Product, StockMovement, Category, StockReservation
from ..services import (
    receive_purchase_order,
    fulfill_sales_order,
    adjustment,
    current_stock,
    available_stock,
    reconcile,
    reserve_stock,
    confirm_reservation,
    release_reservation,
)
from .serializers import (
    ProductSerializer,
    ProductWriteSerializer,
    InboundSerializer,
    OutboundSerializer,
    AdjustmentSerializer,
    ReconcileSerializer,
    MovementSerializer,
    ReserveSerializer,
    ReservationSerializer,
)
from apps.accounts.permissions import RoleBasedPermission
from apps.crm.models import Customer as CRMCustomer
from apps.finance.models import Invoice
from apps.backorder.models import BackOrder
from lib.throttling import StockMutationThrottle

logger = logging.getLogger(__name__)


class ProductListCreateView(generics.ListCreateAPIView):
    permission_classes = [RoleBasedPermission]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductWriteSerializer
        return ProductSerializer

    def get_queryset(self):
        qs = Product.objects.all()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(sku__icontains=search)
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)


class ProductDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [RoleBasedPermission]

    def get_queryset(self):
        return Product.objects.all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProductWriteSerializer
        return ProductSerializer


class InboundView(generics.GenericAPIView):
    serializer_class = InboundSerializer
    permission_classes = [RoleBasedPermission]
    throttle_classes = [StockMutationThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movement = receive_purchase_order(
            product_id=serializer.validated_data["product_id"],
            qty=serializer.validated_data["qty"],
            po_ref=serializer.validated_data["po_ref"],
            user=request.user,
            note=serializer.validated_data.get("note", ""),
            location_id=serializer.validated_data.get("location_id"),
        )
        stock_after = current_stock(movement.product_id)
        logger.info("Inbound success product=%d qty=%d user=%s", movement.product_id, serializer.validated_data["qty"], request.user)
        return Response(
            {"movement_id": movement.id, "product_id": movement.product_id,
             "qty": movement.qty, "stock_after": stock_after,
             "reference": movement.reference},
            status=status.HTTP_201_CREATED,
        )


class OutboundView(generics.GenericAPIView):
    serializer_class = OutboundSerializer
    permission_classes = [RoleBasedPermission]
    throttle_classes = [StockMutationThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = fulfill_sales_order(
            product_id=serializer.validated_data["product_id"],
            qty=serializer.validated_data["qty"],
            so_ref=serializer.validated_data["so_ref"],
            user=request.user,
            note=serializer.validated_data.get("note", ""),
            location_id=serializer.validated_data.get("location_id"),
        )
        movement = result["movement"]
        logger.info("Outbound success product=%d qty=%d user=%s", movement.product_id, serializer.validated_data["qty"], request.user)
        return Response(
            {"movement_id": movement.id, "product_id": movement.product_id,
             "qty": movement.qty, "stock_after": result["stock_after"],
             "reference": movement.reference},
            status=status.HTTP_200_OK,
        )


class AdjustmentView(generics.GenericAPIView):
    serializer_class = AdjustmentSerializer
    permission_classes = [RoleBasedPermission]
    throttle_classes = [StockMutationThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movement = adjustment(
            product_id=serializer.validated_data["product_id"],
            qty=serializer.validated_data["qty"],
            user=request.user,
            reason=serializer.validated_data["reason"],
        )
        stock_after = current_stock(movement.product_id)
        logger.info("Adjustment success product=%d qty=%d user=%s", movement.product_id, serializer.validated_data["qty"], request.user)
        return Response(
            {"movement_id": movement.id, "product_id": movement.product_id,
             "qty": movement.qty, "stock_after": stock_after,
             "reference": movement.reference},
            status=status.HTTP_201_CREATED,
        )


class StockCheckView(generics.GenericAPIView):
    permission_classes = [RoleBasedPermission]

    def get(self, request, product_id):
        stock = current_stock(product_id)
        return Response({"product_id": product_id, "stock": stock})


class ReconcileView(generics.GenericAPIView):
    serializer_class = ReconcileSerializer
    permission_classes = [RoleBasedPermission]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = reconcile(
            product_id=serializer.validated_data["product_id"],
            physical_count=serializer.validated_data["physical_count"],
        )
        return Response(result, status=status.HTTP_200_OK)


class MovementListView(generics.ListAPIView):
    serializer_class = MovementSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self):
        qs = StockMovement.objects.select_related("product", "created_by")
        product_id = self.request.query_params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id)
        movement_type = self.request.query_params.get("type")
        if movement_type:
            qs = qs.filter(type=movement_type)
        return qs[:100]


class DashboardStatsView(generics.GenericAPIView):
    permission_classes = [RoleBasedPermission]

    def get(self, request):
        tenant = request.user.tenant
        now = timezone.now()

        stock_subquery = Subquery(
            StockMovement.objects.filter(
                product_id=OuterRef("pk"), tenant=tenant
            ).values("product_id").annotate(total=Sum("qty")).values("total")[:1],
            output_field=IntegerField(),
        )

        products_qs = Product.objects.filter(tenant=tenant, is_active=True).annotate(
            stock=stock_subquery
        )

        stock_by_category = (
            Product.objects.filter(tenant=tenant, is_active=True)
            .values("category__name")
            .annotate(value=Sum("cost_price"))
            .order_by("-value")
        )

        categories = []
        cat_others = 0
        for i, cat in enumerate(stock_by_category):
            v = float(cat["value"] or 0)
            if i < 6:
                categories.append({"category": cat["category__name"] or "Uncategorized", "value": v})
            else:
                cat_others += v
        if cat_others > 0:
            categories.append({"category": "Others", "value": cat_others})

        movements_all = StockMovement.objects.filter(tenant=tenant)

        months = []
        for i in range(11, -1, -1):
            first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30 * i)
            last = (first + timedelta(days=32)).replace(day=1)
            mvs = movements_all.filter(created_at__gte=first, created_at__lt=last)
            months.append({
                "month": first.strftime("%Y-%m"),
                "inbound": mvs.filter(type="inbound").aggregate(s=Sum("qty"))["s"] or 0,
                "outbound": abs(mvs.filter(type="outbound").aggregate(s=Sum("qty"))["s"] or 0),
                "adjustment": mvs.filter(type="adjustment").aggregate(c=Count("id"))["c"] or 0,
            })

        invoices = Invoice.objects.filter(tenant=tenant)
        revenue_by_month = []
        for i in range(11, -1, -1):
            first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30 * i)
            last = (first + timedelta(days=32)).replace(day=1)
            total = invoices.filter(created_at__gte=first, created_at__lt=last).aggregate(s=Sum("total"))["s"] or 0
            revenue_by_month.append({
                "month": first.strftime("%Y-%m"),
                "revenue": float(total),
            })

        products_with_stock = list(products_qs)
        low_stock_products = [p for p in products_with_stock if (p.stock or 0) <= 5]
        low_stock_list = [
            {"id": p.id, "sku": p.sku, "name": p.name, "stock": p.stock or 0}
            for p in sorted(low_stock_products, key=lambda p: p.stock or 0)[:10]
        ]

        stock_value = sum(float(p.cost_price or 0) * (p.stock or 0) for p in products_with_stock)

        recent = movements_all.select_related("product", "created_by").order_by("-created_at")[:5]
        recent_list = [
            {
                "id": m.id,
                "type": m.type,
                "qty": m.qty,
                "reference": m.reference,
                "product_sku": m.product.sku,
                "product_id": m.product_id,
                "created_by_username": m.created_by.username,
                "created_at": m.created_at,
            }
            for m in recent
        ]

        return Response({
            "stats": {
                "total_products": len(products_with_stock),
                "total_products_all": Product.objects.filter(tenant=tenant).count(),
                "total_customers": CRMCustomer.objects.filter(tenant=tenant).count(),
                "total_invoices": invoices.count(),
                "total_revenue": float(invoices.aggregate(s=Sum("total"))["s"] or 0),
                "open_backorders": BackOrder.objects.filter(
                    tenant=tenant, status__in=["open", "partially_fulfilled"]
                ).count(),
                "stock_value": stock_value,
                "low_stock_count": len(low_stock_products),
            },
            "stock_by_category": categories,
            "movements_by_month": months,
            "revenue_by_month": revenue_by_month,
            "low_stock_products": low_stock_list,
            "recent_movements": recent_list,
        })


class ReserveView(generics.GenericAPIView):
    serializer_class = ReserveSerializer
    permission_classes = [RoleBasedPermission]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        ttl = timedelta(hours=d["ttl_hours"])
        reservation = reserve_stock(
            product_id=d["product_id"],
            qty=d["qty"],
            order_ref=d["order_ref"],
            user=request.user,
            ttl=ttl,
        )
        return Response(
            ReservationSerializer(reservation).data,
            status=status.HTTP_201_CREATED,
        )


class ConfirmReservationView(generics.GenericAPIView):
    permission_classes = [RoleBasedPermission]

    def post(self, request, pk):
        result = confirm_reservation(reservation_id=pk, user=request.user)
        movement = result["movement"]
        return Response({
            "reservation_id": pk,
            "movement_id": movement.id,
            "stock_after": result["stock_after"],
        })


class ReleaseReservationView(generics.GenericAPIView):
    permission_classes = [RoleBasedPermission]

    def post(self, request, pk):
        reason = request.data.get("reason", "")
        reservation = release_reservation(
            reservation_id=pk, user=request.user, reason=reason,
        )
        return Response(ReservationSerializer(reservation).data)


class ReservationListView(generics.ListAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self):
        qs = StockReservation.objects.select_related("product", "created_by")
        product_id = self.request.query_params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id)
        order_ref = self.request.query_params.get("order_ref")
        if order_ref:
            qs = qs.filter(order_ref=order_ref)
        reservation_status = self.request.query_params.get("status")
        if reservation_status:
            qs = qs.filter(status=reservation_status)
        else:
            qs = qs.filter(status=StockReservation.Status.ACTIVE)
        return qs
