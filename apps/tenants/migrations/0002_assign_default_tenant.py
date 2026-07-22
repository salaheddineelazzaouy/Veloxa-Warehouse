from django.db import migrations


def assign_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("tenants", "Tenant")
    User = apps.get_model("accounts", "User")
    default, _ = Tenant.objects.get_or_create(
        slug="default",
        defaults={"name": "Default Tenant"},
    )
    for user in User.objects.filter(tenant__isnull=True):
        user.tenant = default
        user.save(update_fields=["tenant"])

    models_to_assign = [
        ("warehouse", "Product"),
        ("warehouse", "Category"),
        ("warehouse", "Location"),
        ("warehouse", "StockMovement"),
        ("crm", "Customer"),
        ("finance", "Invoice"),
        ("finance", "InvoiceLine"),
        ("backorder", "BackOrder"),
        ("audit", "AuditLog"),
        ("subscriptions", "Subscription"),
        ("subscriptions", "PaymentTransaction"),
    ]
    for app_label, model_name in models_to_assign:
        Model = apps.get_model(app_label, model_name)
        for obj in Model.objects.filter(tenant__isnull=True):
            if hasattr(obj, "created_by") and obj.created_by and obj.created_by.tenant:
                obj.tenant = obj.created_by.tenant
            elif hasattr(obj, "user") and obj.user and obj.user.tenant:
                obj.tenant = obj.user.tenant
            else:
                obj.tenant = default
            obj.save(update_fields=["tenant"])


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0001_initial"),
        ("accounts", "0002_user_tenant"),
        ("warehouse", "0003_alter_location_options_category_tenant_and_more"),
        ("crm", "0002_customer_tenant"),
        ("finance", "0002_invoice_tenant_invoiceline_tenant"),
        ("backorder", "0002_backorder_tenant"),
        ("audit", "0002_auditlog_tenant"),
        ("subscriptions", "0002_paymenttransaction_tenant_subscription_tenant"),
    ]

    operations = [
        migrations.RunPython(assign_default_tenant),
    ]
