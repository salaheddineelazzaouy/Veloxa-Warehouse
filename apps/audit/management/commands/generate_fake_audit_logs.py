import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from random import randint, choice
from faker import Faker
from apps.audit.models import AuditLog
from apps.tenants.models import Tenant

logging.getLogger("faker").setLevel(logging.WARNING)
fake = Faker(["fr_FR"])

User = get_user_model()


class Command(BaseCommand):
    help = "Generate N fake audit log entries"

    def add_arguments(self, parser):
        parser.add_argument("count", nargs="?", type=int, default=500)
        parser.add_argument("--clear", action="store_true", help="Clear existing audit logs first")

    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]

        tenant = Tenant.objects.first()
        if not tenant:
            self.stdout.write(self.style.ERROR("No tenant found. Run seed_data first."))
            return

        users = list(User.objects.filter(tenant=tenant))
        if not users:
            self.stdout.write(self.style.ERROR("No users found. Run seed_data first."))
            return

        if clear:
            deleted = AuditLog.objects.filter(tenant=tenant).delete()
            self.stdout.write(f"Cleared {deleted[0]} audit logs.")

        now = timezone.now()
        actions = ["create", "create", "update", "update", "update", "delete", "read_pii"]
        tables = [
            "warehouse_product",
            "warehouse_stockmovement",
            "crm_customer",
            "finance_invoice",
            "finance_invoiceline",
            "backorder_backorder",
            "accounts_user",
        ]
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
        ]
        ips = [fake.ipv4() for _ in range(20)]

        change_templates = {
            "create": lambda: {
                "fields_created": choice([
                    ["name", "sku", "cost_price"],
                    ["name", "email", "phone"],
                    ["invoice_ref", "total", "customer"],
                    ["product", "qty", "type"],
                ]),
                "new_values": {"name": fake.company(), "created": True},
            },
            "update": lambda: {
                "field": choice(["name", "cost_price", "email", "phone", "status", "address"]),
                "old": fake.word(),
                "new": fake.word(),
            },
            "delete": lambda: {
                "deleted_id": randint(1, 9999),
                "soft_delete": choice([True, False]),
            },
            "read_pii": lambda: {
                "fields_accessed": choice([
                    ["phone", "email", "address"],
                    ["ice", "identifiant_fiscal"],
                    ["phone"],
                ]),
                "reason": choice(["customer_lookup", "invoice_view", "profile_check"]),
            },
        }

        with transaction.atomic():
            created = 0
            for _ in range(count):
                days_ago = randint(0, 365)
                log_time = now - timedelta(
                    days=days_ago,
                    hours=randint(0, 23),
                    minutes=randint(0, 59),
                    seconds=randint(0, 59),
                )
                action = choice(actions)
                table = choice(tables)

                audit = AuditLog(
                    user=choice(users),
                    action=action,
                    table_name=table,
                    row_id=randint(1, 9999) if action != "read_pii" else None,
                    changes=change_templates[action](),
                    ip_address=choice(ips),
                    user_agent=choice(user_agents),
                    tenant=tenant,
                )
                audit.timestamp = log_time
                audit.save()
                created += 1

        self.stdout.write(self.style.SUCCESS(f"{created} fake audit logs created."))
