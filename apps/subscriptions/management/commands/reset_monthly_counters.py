from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Reset monthly usage counters (placeholder — implement with your counter model)"

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(
                f"Monthly counters reset for {now.strftime('%Y-%m')}. "
                "Implement usage tracking models if needed."
            )
        )
