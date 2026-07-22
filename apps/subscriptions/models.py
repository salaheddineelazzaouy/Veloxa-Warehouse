from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.tenants.managers import TenantAwareManager


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price_monthly = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    price_yearly = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True, validators=[MinValueValidator(Decimal("0.01"))]
    )
    is_active = models.BooleanField(default=True)
    features = models.JSONField(
        default=dict,
        help_text=(
            "Store key-value pairs of limitations. "
            "Example: {\"max_products\": 100, \"max_users\": 5, "
            "\"max_stock_movements_per_month\": 10000, "
            "\"backorder_tracking\": true, \"audit_log_retention_days\": 30}"
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price_monthly"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("canceled", "Canceled"),
        ("pending_payment", "Pending Payment"),
    ]
    BILLING_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="subscriptions"
    )
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL,
        null=True, related_name="subscriptions"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending_payment"
    )
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    billing_cycle = models.CharField(
        max_length=10, choices=BILLING_CHOICES, default="monthly"
    )
    last_payment_date = models.DateTimeField(blank=True, null=True)
    next_payment_date = models.DateTimeField(blank=True, null=True)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="%(class)s_set",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantAwareManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.plan} ({self.status})"


def proof_upload_path(instance, filename):
    return f"payments/{instance.user.id}/{instance.reference_number}/{filename}"


class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="payment_transactions"
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="payments"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    currency = models.CharField(max_length=3, default="MAD")
    payment_method = models.CharField(max_length=50, default="bank_transfer")
    reference_number = models.CharField(
        max_length=100, unique=True,
        help_text="User-provided or generated reference"
    )
    proof_image = models.FileField(
        upload_to=proof_upload_path,
        help_text="Upload bank receipt / proof of transfer"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="verified_payments"
    )
    verified_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Plan the user intends to subscribe to"
    )
    billing_cycle = models.CharField(
        max_length=10, choices=Subscription.BILLING_CHOICES,
        default="monthly"
    )
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="%(class)s_set",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantAwareManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.reference_number} ({self.status})"
