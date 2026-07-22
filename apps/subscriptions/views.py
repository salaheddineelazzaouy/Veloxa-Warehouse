from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import SubscriptionPlan, PaymentTransaction
from .serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer,
    PaymentTransactionSerializer, PaymentRequestSerializer,
)
from .utils import get_active_subscription, get_user_limits


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]


class PublicPlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]


class SubscriptionViewSet(viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_active_subscription(self.request.user)

    @action(detail=False, methods=["get"], url_path="my-subscription")
    def my_subscription(self, request):
        sub = request.user.subscriptions.order_by("-created_at").first()
        if sub is None:
            return Response(
                {"detail": "No subscription found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        limits = get_user_limits(request.user)
        serializer = self.get_serializer(sub)
        data = serializer.data
        data["remaining_limits"] = limits if sub.status == "active" else {}
        return Response(data)

    @action(detail=False, methods=["post"], url_path="request-payment")
    def request_payment(self, request):
        serializer = PaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = SubscriptionPlan.objects.get(
            id=serializer.validated_data["plan_id"]
        )
        billing_cycle = serializer.validated_data["billing_cycle"]
        amount = (
            plan.price_yearly
            if billing_cycle == "yearly" and plan.price_yearly
            else plan.price_monthly
        )
        txn = PaymentTransaction.objects.create(
            user=request.user,
            amount=amount,
            reference_number=serializer.validated_data["reference_number"],
            proof_image=serializer.validated_data["proof_image"],
            notes=serializer.validated_data.get("notes", ""),
            plan=plan,
            billing_cycle=billing_cycle,
            tenant=request.user.tenant,
        )
        return Response(
            PaymentTransactionSerializer(txn).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="payment-history")
    def payment_history(self, request):
        txns = PaymentTransaction.objects.filter(user=request.user)
        return Response(
            PaymentTransactionSerializer(txns, many=True).data
        )

    @action(detail=False, methods=["post"], url_path="check-limits")
    def check_limits(self, request):
        limit_key = request.data.get("limit_key")
        current_usage = request.data.get("current_usage", 0)
        increment = request.data.get("increment", 0)
        sub = get_active_subscription(request.user)
        if sub is None:
            return Response({
                "allowed": False,
                "message": "No active subscription",
                "limit_key": limit_key,
                "max_limit": 0,
                "current_usage": current_usage,
                "increment": increment,
            })
        limits = get_user_limits(request.user)
        allowed = True
        message = "OK"
        max_limit = None
        if limit_key and limit_key in limits:
            max_limit = limits[limit_key]
            if isinstance(max_limit, bool):
                allowed = max_limit
                if not allowed:
                    message = f"Feature '{limit_key}' is not available on your plan"
            else:
                try:
                    max_limit_int = int(max_limit)
                    if current_usage + increment > max_limit_int:
                        allowed = False
                        message = (
                            f"Limit reached for '{limit_key}' "
                            f"({current_usage + increment}/{max_limit})"
                        )
                except (ValueError, TypeError):
                    pass
        elif limit_key:
            allowed = False
            message = f"Feature '{limit_key}' is not defined on your plan"
        return Response({
            "allowed": allowed,
            "message": message,
            "limit_key": limit_key,
            "max_limit": max_limit,
            "current_usage": current_usage,
            "increment": increment,
        })
