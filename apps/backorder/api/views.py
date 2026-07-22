import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import BackOrder
from ..services import create_backorder, fulfill_backorder
from .serializers import BackOrderSerializer, BackOrderCreateSerializer, FulfillSerializer
from lib.throttling import BackorderThrottle

logger = logging.getLogger(__name__)


class BackOrderListView(generics.ListCreateAPIView):
    queryset = BackOrder.objects.select_related("product").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BackOrderCreateSerializer
        return BackOrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        bo = create_backorder(
            product_id=serializer.validated_data["product_id"],
            missing_qty=serializer.validated_data["qty"],
            so_ref=serializer.validated_data.get("sales_order_ref", ""),
            user=self.request.user,
        )
        return bo

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bo = self.perform_create(serializer)
        out_serializer = BackOrderSerializer(bo)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class FulfillBackOrderView(generics.GenericAPIView):
    serializer_class = FulfillSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [BackorderThrottle]

    def post(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            bo = fulfill_backorder(pk, serializer.validated_data["qty"], request.user)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BackOrderSerializer(bo).data)
