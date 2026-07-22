import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Invoice
from ..services import create_invoice, update_invoice, delete_invoice, calculate_cogs
from .serializers import InvoiceSerializer, InvoiceCreateSerializer

logger = logging.getLogger(__name__)


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Invoice.objects.prefetch_related("lines").all()
        customer_id = self.request.query_params.get("customer_id")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs


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
            tenant=request.user.tenant,
        )
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Invoice.objects.prefetch_related("lines__product").all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        invoice = self.get_object()
        data = request.data
        invoice = update_invoice(
            invoice_id=invoice.id,
            order_ref=data.get("order_ref"),
            customer_id=data.get("customer_id"),
            source=data.get("source"),
            lines=data.get("lines"),
            user=request.user,
        )
        return Response(InvoiceSerializer(invoice).data)

    def destroy(self, request, *args, **kwargs):
        invoice = self.get_object()
        delete_invoice(invoice.id, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class COGSView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        cogs = calculate_cogs(product_id)
        return Response({"product_id": product_id, "cogs": str(cogs)})
