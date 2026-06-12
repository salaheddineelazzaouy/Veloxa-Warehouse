import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Invoice
from ..services import create_invoice, calculate_cogs
from .serializers import InvoiceSerializer, InvoiceCreateSerializer

logger = logging.getLogger(__name__)


class InvoiceListView(generics.ListAPIView):
    queryset = Invoice.objects.prefetch_related("lines").all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]


class InvoiceCreateView(generics.GenericAPIView):
    serializer_class = InvoiceCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = create_invoice(
            order_ref=serializer.validated_data["order_ref"],
            lines=serializer.validated_data["lines"],
            user=request.user,
            customer_id=serializer.validated_data.get("customer_id"),
        )
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


class COGSView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        cogs = calculate_cogs(product_id)
        return Response({"product_id": product_id, "cogs": str(cogs)})
