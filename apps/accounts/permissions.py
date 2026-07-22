from django.contrib.auth.models import Group, Permission

WAREHOUSE_PERMISSIONS = {
    "warehouse_manager": [
        "warehouse.add_stockmovement",
        "warehouse.view_stockmovement",
        "warehouse.add_adjustment",
        "backorder.add_backorder",
        "backorder.view_backorder",
    ],
    "auditor": [
        "warehouse.view_stockmovement",
        "warehouse.view_product",
        "audit.view_auditlog",
        "audit.run_reconciliation",
    ],
    "viewer": [
        "warehouse.view_stockmovement",
        "warehouse.view_product",
    ],
}


def setup_groups():
    for group_name, perms in WAREHOUSE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        for perm_codename in perms:
            try:
                perm = Permission.objects.get(codename=perm_codename)
                group.permissions.add(perm)
            except Permission.DoesNotExist:
                pass
