from __future__ import annotations

from decimal import Decimal

from django.db.models import QuerySet, Sum
from django.db.models.functions import Coalesce

from apps.clients.models import Client
from apps.expenses.models import Expense
from apps.invoices.models import Invoice, Payment
from apps.services.pricing import quantize_money


class ClientSelector:
    @staticmethod
    def all() -> QuerySet[Client]:
        return Client.objects.all()

    @staticmethod
    def by_id(*, client_id: int) -> Client:
        return Client.objects.get(pk=client_id)

    @staticmethod
    def statement(*, client: Client) -> dict:
        invoices = list(
            Invoice.objects.filter(client=client)
            .exclude(status=Invoice.Status.DRAFT)
            .order_by("-issue_date", "-id")
        )
        deposits = list(
            Payment.objects.filter(client=client)
            .select_related("invoice")
            .order_by("-paid_at", "-id")
        )

        charged = Invoice.objects.filter(
            client=client, status=Invoice.Status.CONFIRMED
        ).aggregate(total=Coalesce(Sum("total"), Decimal("0")))["total"]
        deposited = Payment.objects.filter(client=client).aggregate(
            total=Coalesce(Sum("amount"), Decimal("0"))
        )["total"]
        expenses_total = Expense.objects.filter(client=client).aggregate(
            total=Coalesce(Sum("amount"), Decimal("0"))
        )["total"]
        charged = quantize_money(charged)
        deposited = quantize_money(deposited)
        balance_due = quantize_money(charged - deposited)

        return {
            "client": client,
            "total_charged": charged,
            "total_deposits": deposited,
            "balance_due": balance_due,
            "total_expenses": quantize_money(expenses_total),
            "invoices": invoices,
            "deposits": deposits,
        }
