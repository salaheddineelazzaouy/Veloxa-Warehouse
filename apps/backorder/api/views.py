import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import BackOrder
from ..services import fulfill_backorder
from .serializers import BackOrderSerializer, FulfillSerializer
from lib.throttling import BackorderThrottle

logger = logging.getLogger(__name__)


class BackOrderListView(generics.ListAPIView):
    queryset = BackOrder.objects.select_related("product").all()
    serializer_class = BackOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


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
