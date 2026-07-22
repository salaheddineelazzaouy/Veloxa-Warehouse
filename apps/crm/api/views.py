import logging
from rest_framework import generics
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
        qs = Customer.objects.all()
        search = self.request.query_params.get("search")
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(ice__icontains=search) |
                Q(identifiant_fiscal__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        customer = create_customer(
            tenant=self.request.user.tenant,
            name=serializer.validated_data["name"],
            ice=serializer.validated_data.get("ice", ""),
            identifiant_fiscal=serializer.validated_data.get("identifiant_fiscal", ""),
            taxe_professionnelle=serializer.validated_data.get("taxe_professionnelle", ""),
            registre_commerce=serializer.validated_data.get("registre_commerce", ""),
            phone=serializer.validated_data.get("phone", ""),
            email=serializer.validated_data.get("email", ""),
            address=serializer.validated_data.get("address", ""),
            metadata=serializer.validated_data.get("metadata", {}),
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
