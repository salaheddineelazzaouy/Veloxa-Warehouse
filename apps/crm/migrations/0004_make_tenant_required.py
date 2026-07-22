# Generated manually — all existing rows have a tenant assigned

import django.db.models.deletion
from django.db import migrations, models


def assign_default_tenant(apps, schema_editor):
    Customer = apps.get_model("crm", "Customer")
    Tenant = apps.get_model("tenants", "Tenant")
    default = Tenant.objects.first()
    if default:
        Customer.objects.filter(tenant__isnull=True).update(tenant=default)


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0003_add_new_customer_fields"),
    ]

    operations = [
        migrations.RunPython(assign_default_tenant, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="customer",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="customers",
                to="tenants.tenant",
            ),
        ),
    ]
