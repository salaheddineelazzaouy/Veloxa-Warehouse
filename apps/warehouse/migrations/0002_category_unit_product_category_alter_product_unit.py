from django.db import migrations, models
import django.db.models.deletion


def create_default_units(apps, schema_editor):
    Unit = apps.get_model("warehouse", "Unit")
    defaults = [
        ("Piece", "pcs"), ("Box", "box"), ("Pack", "pack"),
        ("Unit", "unit"), ("Kilogram", "kg"), ("Meter", "m"),
        ("Liter", "l"), ("Set", "set"), ("Pair", "pair"),
    ]
    for name, abbr in defaults:
        Unit.objects.get_or_create(name=name, defaults={"abbreviation": abbr})


def migrate_unit_data(apps, schema_editor):
    Product = apps.get_model("warehouse", "Product")
    Unit = apps.get_model("warehouse", "Unit")
    unit_map = {}
    for u in Unit.objects.all():
        unit_map[u.abbreviation.lower()] = u
    pcs = Unit.objects.filter(abbreviation="pcs").first()
    for product in Product.objects.all():
        old = product.unit
        if isinstance(old, str) and old.lower() in unit_map:
            product.unit_new = unit_map[old.lower()]
        elif pcs:
            product.unit_new = pcs
        product.save(update_fields=["unit_new"])


class Migration(migrations.Migration):

    dependencies = [
        ("warehouse", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name_plural": "Categories",
                "db_table": "warehouse_category",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Unit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="e.g. Kilogram, Piece, Box", max_length=50, unique=True)),
                ("abbreviation", models.CharField(help_text="e.g. kg, pcs, box", max_length=10, unique=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "warehouse_unit",
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(create_default_units),
        migrations.AddField(
            model_name="product",
            name="category",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="products", to="warehouse.category"),
        ),
        migrations.AddField(
            model_name="product",
            name="unit_new",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="products", to="warehouse.unit"),
        ),
        migrations.RunPython(migrate_unit_data),
        migrations.RemoveField(
            model_name="product",
            name="unit",
        ),
        migrations.RenameField(
            model_name="product",
            old_name="unit_new",
            new_name="unit",
        ),
    ]
