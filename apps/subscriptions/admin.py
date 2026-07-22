from django.contrib import admin, messages
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, Subscription, PaymentTransaction


@admin.action(description="Verify selected payments and activate subscriptions")
def verify_payments(modeladmin, request, queryset):
    verified_count = 0
    for txn in queryset.filter(status="pending"):
        plan = txn.plan or (
            txn.subscription.plan if txn.subscription else None
        )
        if plan is None:
            modeladmin.message_user(
                request,
                f"Transaction {txn.reference_number}: no plan associated, skipped.",
                level=messages.WARNING,
            )
            continue
        billing_cycle = txn.billing_cycle
        delta = (
            timedelta(days=365)
            if billing_cycle == "yearly"
            else timedelta(days=30)
        )
        now = timezone.now()
        if txn.subscription and txn.subscription.status == "active":
            sub = txn.subscription
            new_end = (sub.end_date or now) + delta
            sub.end_date = new_end
            sub.next_payment_date = new_end
            sub.last_payment_date = now
            sub.save()
        else:
            sub, _ = Subscription.objects.update_or_create(
                user=txn.user,
                defaults={
                    "plan": plan,
                    "status": "active",
                    "start_date": now,
                    "end_date": now + delta,
                    "billing_cycle": billing_cycle,
                    "last_payment_date": now,
                    "next_payment_date": now + delta,
                },
            )
        txn.status = "verified"
        txn.verified_by = request.user
        txn.verified_at = now
        txn.subscription = sub
        txn.save()
        verified_count += 1
    modeladmin.message_user(
        request,
        f"{verified_count} payment(s) verified and subscription(s) activated.",
    )


@admin.action(description="Reject selected payments")
def reject_payments(modeladmin, request, queryset):
    updated = queryset.filter(status="pending").update(
        status="rejected", verified_by=request.user, verified_at=timezone.now()
    )
    modeladmin.message_user(
        request, f"{updated} payment(s) rejected."
    )


class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        "name", "price_monthly", "price_yearly", "is_active",
    ]
    list_filter = ["is_active"]
    search_fields = ["name"]
    fieldsets = [
        (None, {"fields": ["name", "description"]}),
        ("Pricing", {"fields": ["price_monthly", "price_yearly"]}),
        ("Settings", {"fields": ["is_active", "features"]}),
    ]


class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "user", "reference_number", "amount", "currency",
        "status", "plan", "billing_cycle", "created_at",
    ]
    list_filter = ["status", "created_at", "verified_by"]
    search_fields = [
        "user__username", "user__email", "reference_number",
    ]
    actions = [verify_payments, reject_payments]
    readonly_fields = [
        "user", "subscription", "amount", "currency", "payment_method",
        "reference_number", "status", "verified_by", "verified_at",
        "created_at", "plan", "billing_cycle",
    ]
    fieldsets = [
        ("Transaction", {
            "fields": [
                "user", "subscription", "reference_number", "amount",
                "currency", "payment_method",
            ],
        }),
        ("Plan Info", {"fields": ["plan", "billing_cycle"]}),
        ("Proof", {"fields": ["proof_image"]}),
        ("Status", {
            "fields": ["status", "verified_by", "verified_at", "notes"],
        }),
    ]


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "user", "plan", "status", "billing_cycle",
        "start_date", "end_date",
    ]
    list_filter = ["status", "billing_cycle", "plan"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at"]


admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(PaymentTransaction, PaymentTransactionAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
