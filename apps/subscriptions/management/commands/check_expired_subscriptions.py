from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.subscriptions.models import Subscription
from apps.tenants.utils import bypass_tenant


class Command(BaseCommand):
    help = "Set subscriptions to expired when end_date has passed"

    def handle(self, *args, **options):
        with bypass_tenant():
            now = timezone.now()
            expired = Subscription.objects.filter(
                status="active", end_date__lt=now
            )
            count = expired.count()
            expired.update(status="expired")
            self.stdout.write(
                self.style.SUCCESS(f"{count} subscription(s) marked as expired.")
            )
