import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from random import choice, randint
from faker import Faker
from apps.tenants.models import Tenant
from apps.tenants.utils import bypass_tenant

logging.getLogger("faker").setLevel(logging.WARNING)

User = get_user_model()
fake = Faker(["fr_FR"])


class Command(BaseCommand):
    help = "Generate fake users with various roles"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=20, help="Number of users to create")
        parser.add_argument("--clear", action="store_true", help="Delete all non-superuser users first")

    def handle(self, *args, **options):
        with bypass_tenant():
            count = options["count"]
            clear = options["clear"]

            tenant = Tenant.objects.filter(slug="default").first()
            if not tenant:
                tenant, _ = Tenant.objects.get_or_create(slug="default", defaults={"name": "Default Tenant"})

            if clear:
                User.objects.filter(is_superuser=False).delete()
                self.stdout.write(self.style.WARNING("Cleared all non-superuser users."))

            roles = [
                ("super_admin", 1),
                ("warehouse_manager", 4),
                ("auditor", 3),
                ("viewer", 12),
            ]

            created = 0
            with transaction.atomic():
                for role, role_count in roles:
                    for i in range(role_count):
                        first_name = fake.first_name()
                        last_name = fake.last_name()
                        username = f"{first_name.lower()}.{last_name.lower()}.{randint(10,99)}"
                        email = f"{username}@{fake.free_email_domain()}"

                        if User.objects.filter(username=username).exists():
                            continue

                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password="pass1234",
                            first_name=first_name,
                            last_name=last_name,
                        )
                        user.role = role
                        user.tenant = tenant
                        user.is_active = True
                        user.save(update_fields=["role", "tenant", "is_active"])
                        created += 1

            total = User.objects.count()
            self.stdout.write(self.style.SUCCESS(f"Created {created} users. Total: {total}"))
