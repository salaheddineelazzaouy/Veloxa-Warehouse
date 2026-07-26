from django.core.management.base import BaseCommand
from apps.tenants.utils import bypass_tenant
from apps.finance.models import Invoice, InvoiceLine
from apps.finance.number_to_french import number_to_french
from decimal import Decimal


class Command(BaseCommand):
    help = "Backfill VAT totals on old invoices"

    def handle(self, *args, **options):
        with bypass_tenant():
            lines = list(InvoiceLine.objects.all())
            self.stdout.write(f"{len(lines)} lines found")

            updated_lines = 0
            updated_invoices = set()

            for line in lines:
                ht = line.qty * line.unit_price
                vat = ht * line.vat_rate
                ttc = ht + vat
                if line.total_ht != ht or line.total_vat != vat or line.total_ttc != ttc:
                    InvoiceLine.objects.filter(pk=line.pk).update(
                        total_ht=ht, total_vat=vat, total_ttc=ttc, total=ttc,
                    )
                    updated_lines += 1
                    updated_invoices.add(line.invoice_id)

            self.stdout.write(f"Backfilled {updated_lines} lines across {len(updated_invoices)} invoices")

            for inv_id in updated_invoices:
                inv_lines = InvoiceLine.objects.filter(invoice_id=inv_id)
                total_ht = Decimal("0")
                total_vat = Decimal("0")
                for l in inv_lines:
                    total_ht += l.total_ht
                    total_vat += l.total_vat
                total_ttc = total_ht + total_vat
                Invoice.objects.filter(pk=inv_id).update(
                    total_ht=total_ht,
                    total_vat=total_vat,
                    total_ttc=total_ttc,
                    total=total_ttc,
                    amount_in_words=number_to_french(total_ttc),
                )

            self.stdout.write(self.style.SUCCESS(f"Recomputed {len(updated_invoices)} invoices"))
