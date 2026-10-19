from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.expenses.models import Expense
from apps.invoices.models import Invoice
from apps.services.pricing import quantize_money


def _sum(qs, field: str) -> Decimal:
    return quantize_money(qs.aggregate(t=Coalesce(Sum(field), Decimal("0")))["t"])


def get_statistics(*, today: date | None = None) -> dict:
    """Business totals. Bills = confirmed invoices; profit = bills - expenses."""
    today = today or timezone.localdate()
    invoices = Invoice.objects.filter(status=Invoice.Status.CONFIRMED)
    expenses = Expense.objects.all()

    total_invoices = _sum(invoices, "total")
    total_expenses = _sum(expenses, "amount")

    month_invoices = _sum(
        invoices.filter(issue_date__year=today.year, issue_date__month=today.month),
        "total",
    )
    month_expenses = _sum(
        expenses.filter(
            expense_date__year=today.year, expense_date__month=today.month
        ),
        "amount",
    )
    year_invoices = _sum(invoices.filter(issue_date__year=today.year), "total")
    year_expenses = _sum(expenses.filter(expense_date__year=today.year), "amount")

    return {
        "total_invoices": total_invoices,
        "total_expenses": total_expenses,
        "current_money": quantize_money(total_invoices - total_expenses),
        "month": {
            "invoices": month_invoices,
            "expenses": month_expenses,
            "profit": quantize_money(month_invoices - month_expenses),
        },
        "year": {
            "invoices": year_invoices,
            "expenses": year_expenses,
            "profit": quantize_money(year_invoices - year_expenses),
        },
    }
