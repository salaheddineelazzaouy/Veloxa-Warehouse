from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.subscriptions.models import Subscription
from apps.tenants.utils import bypass_tenant


class Command(BaseCommand):
    help = "Email users whose subscription will expire in 7 days"

    def handle(self, *args, **options):
        with bypass_tenant():
            now = timezone.now()
            warning_date = now + timedelta(days=7)
            expiring = Subscription.objects.filter(
                status="active",
                end_date__lte=warning_date,
                end_date__gte=now,
            )
            count = 0
            for sub in expiring:
                if sub.user.email:
                    try:
                        from django.core.mail import send_mail
                        send_mail(
                            subject="Your Veloxa subscription is expiring soon",
                            message=(
                                f"Hi {sub.user.username},\n\n"
                                f"Your {sub.plan.name} subscription will expire "
                                f"on {sub.end_date.strftime('%Y-%m-%d')}.\n"
                                "Please renew to avoid service interruption.\n\n"
                                "— Veloxa Team"
                            ),
                            from_email=None,
                            recipient_list=[sub.user.email],
                            fail_silently=True,
                        )
                        count += 1
                    except Exception as e:
                        self.stderr.write(
                            f"Failed to email {sub.user.email}: {e}"
                        )
            self.stdout.write(
                self.style.SUCCESS(
                    f"{count} reminder email(s) sent."
                )
            )
