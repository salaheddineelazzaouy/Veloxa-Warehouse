import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Product, StockMovement
from ..services import (
    receive_purchase_order,
    fulfill_sales_order,
    adjustment,
    current_stock,
    reconcile,
)
from .serializers import (
    ProductSerializer,
    ProductWriteSerializer,
    InboundSerializer,
    OutboundSerializer,
    AdjustmentSerializer,
    ReconcileSerializer,
    MovementSerializer,
)
from lib.throttling import StockMutationThrottle

logger = logging.getLogger(__name__)


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated]

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


class ProductDetailView(generics.RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProductWriteSerializer
        return ProductSerializer


class InboundView(generics.GenericAPIView):
    serializer_class = InboundSerializer
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        stock = current_stock(product_id)
        return Response({"product_id": product_id, "stock": stock})


class ReconcileView(generics.GenericAPIView):
    serializer_class = ReconcileSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = StockMovement.objects.select_related("product", "created_by")
        product_id = self.request.query_params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id)
        movement_type = self.request.query_params.get("type")
        if movement_type:
            qs = qs.filter(type=movement_type)
        return qs[:100]
