from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce, TruncDay, TruncMonth
from django.utils import timezone

from apps.expenses.models import Expense
from apps.invoices.models import Invoice, Payment
from apps.services.pricing import quantize_money


def _sum(qs, field: str) -> Decimal:
    return quantize_money(qs.aggregate(t=Coalesce(Sum(field), Decimal("0")))["t"])


def _series(qs, date_field: str, value_field: str, trunc) -> dict:
    rows = (
        qs.annotate(bucket=trunc(date_field))
        .values("bucket")
        .annotate(t=Sum(value_field))
    )
    return {r["bucket"]: quantize_money(r["t"] or Decimal("0")) for r in rows}


def _period(
    *, date_from: date, date_to: date, invoices, payments, expenses
) -> dict:
    inv = invoices.filter(issue_date__gte=date_from, issue_date__lte=date_to)
    pay = payments.filter(paid_at__gte=date_from, paid_at__lte=date_to)
    exp = expenses.filter(expense_date__gte=date_from, expense_date__lte=date_to)

    by_month = (date_to - date_from).days > 62
    trunc = TruncMonth if by_month else TruncDay
    inv_s = _series(inv, "issue_date", "total", trunc)
    pay_s = _series(pay, "paid_at", "amount", trunc)
    exp_s = _series(exp, "expense_date", "amount", trunc)

    zero = quantize_money(Decimal("0"))
    buckets: list[date] = []
    cur = date_from.replace(day=1) if by_month else date_from
    while cur <= date_to:
        buckets.append(cur)
        if by_month:
            cur = (cur + timedelta(days=monthrange(cur.year, cur.month)[1])).replace(
                day=1
            )
        else:
            cur += timedelta(days=1)

    def _get(series: dict, key: date) -> Decimal:
        # TruncDay/TruncMonth on DateField yields date objects.
        return series.get(key, zero)

    total_inv = _sum(inv, "total")
    total_pay = _sum(pay, "amount")
    total_exp = _sum(exp, "amount")
    return {
        "date_from": date_from,
        "date_to": date_to,
        "invoices": total_inv,
        "payments": total_pay,
        "expenses": total_exp,
        "profit": quantize_money(total_inv - total_exp),
        "group": "month" if by_month else "day",
        "series": [
            {
                "date": b,
                "invoices": _get(inv_s, b),
                "payments": _get(pay_s, b),
                "expenses": _get(exp_s, b),
            }
            for b in buckets
        ],
    }


def get_statistics(
    *,
    today: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    """Business totals. Bills = confirmed invoices; profit = bills - expenses.

    ``period`` covers ``date_from..date_to`` (default: current month).
    """
    today = today or timezone.localdate()
    if date_from is None and date_to is None:
        date_from = today.replace(day=1)
        date_to = today.replace(day=monthrange(today.year, today.month)[1])
    date_from = date_from or date_to
    date_to = date_to or date_from
    if date_from > date_to:
        date_from, date_to = date_to, date_from
    payments = Payment.objects.all()
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

    today_payments = _sum(payments.filter(paid_at=today), "amount")
    today_expenses = _sum(expenses.filter(expense_date=today), "amount")

    period = _period(
        date_from=date_from,
        date_to=date_to,
        invoices=invoices,
        payments=payments,
        expenses=expenses,
    )

    return {
        "period": period,
        "total_invoices": total_invoices,
        "total_expenses": total_expenses,
        "today": {
            "date": today,
            "payments": today_payments,
            "expenses": today_expenses,
            "cash": quantize_money(today_payments - today_expenses),
        },
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
