import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Customer
from ..services import anonymize_customer, create_customer
from .serializers import CustomerSerializer, CustomerWriteSerializer

logger = logging.getLogger(__name__)


class CustomerListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CustomerWriteSerializer
        return CustomerSerializer

    def get_queryset(self):
        return Customer.objects.all()

    def perform_create(self, serializer):
        customer = create_customer(
            name=serializer.validated_data["name"],
            phone=serializer.validated_data.get("phone", ""),
            email=serializer.validated_data.get("email", ""),
            address=serializer.validated_data.get("address", ""),
            created_by=self.request.user,
        )
        return customer


class CustomerDetailView(generics.RetrieveUpdateAPIView):
    queryset = Customer.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CustomerWriteSerializer
        return CustomerSerializer


class AnonymizeCustomerView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        customer = anonymize_customer(pk, request.user)
        return Response(CustomerSerializer(customer).data)
