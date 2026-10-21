from decimal import Decimal

from django.db.models import Count, F, QuerySet, Sum

from apps.expenses.models import Expense
from apps.invoices.models import Invoice, InvoiceItem
from apps.services.models import Service, ServiceCategory


class ServiceCategorySelector:
    @staticmethod
    def all() -> QuerySet[ServiceCategory]:
        return ServiceCategory.objects.select_related("expense_category").all()

    @staticmethod
    def by_id(*, category_id: int) -> ServiceCategory:
        return ServiceCategory.objects.select_related("expense_category").get(
            pk=category_id
        )

    @staticmethod
    def invoice_stats(*, category: ServiceCategory, last: int = 5) -> dict:
        """Confirmed invoices containing this category's services.

        The amount is the category's own share of those invoices
        (``line_total × piece.quantity`` of its items), not the whole invoice total.
        """
        items = InvoiceItem.objects.filter(
            service__service_category=category,
            invoice__status=Invoice.Status.CONFIRMED,
        )
        share = F("line_total") * F("piece__quantity")
        total = items.aggregate(total=Sum(share))["total"] or Decimal("0")
        invoice_ids = items.values_list("invoice_id", flat=True).distinct()
        invoices = Invoice.objects.filter(pk__in=invoice_ids)
        last_invoices = []
        for invoice in invoices.select_related("client").order_by(
            "-issue_date", "-id"
        )[:last]:
            amount = items.filter(invoice=invoice).aggregate(a=Sum(share))["a"]
            last_invoices.append(
                {
                    "id": invoice.id,
                    "number": invoice.number,
                    "client_name": invoice.client.name,
                    "issue_date": invoice.issue_date,
                    "invoice_total": invoice.total,
                    "category_amount": amount or Decimal("0"),
                }
            )
        return {
            "invoices_count": invoices.count(),
            "invoices_total": total,
            "last_invoices": last_invoices,
        }

    @staticmethod
    def expense_stats(*, category: ServiceCategory) -> dict:
        if category.expense_category_id is None:
            return {"expenses_count": 0, "expenses_total": Decimal("0")}
        agg = Expense.objects.filter(
            category_id=category.expense_category_id
        ).aggregate(count=Count("id"), total=Sum("amount"))
        return {
            "expenses_count": agg["count"],
            "expenses_total": agg["total"] or Decimal("0"),
        }


class ServiceSelector:
    @staticmethod
    def all() -> QuerySet[Service]:
        return Service.objects.select_related("service_category").all()

    @staticmethod
    def by_id(*, service_id: int) -> Service:
        return Service.objects.select_related("service_category").get(pk=service_id)
