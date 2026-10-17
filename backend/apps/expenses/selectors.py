from typing import Any

from django.db.models import QuerySet, Sum

from apps.expenses.filters import ExpenseFilter
from apps.expenses.models import Expense


def get_expenses(*, filters: dict[str, Any] | None = None) -> QuerySet[Expense]:
    filters = filters or {}
    qs = Expense.objects.select_related("service_category").all()
    return ExpenseFilter(filters, qs).qs


def get_expenses_summary(*, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    qs = get_expenses(filters=filters)

    total = qs.aggregate(Sum("amount"))["amount__sum"] or 0

    factory = (
        qs.filter(category=Expense.Category.FACTORY).aggregate(Sum("amount"))[
            "amount__sum"
        ]
        or 0
    )
    salaries = (
        qs.filter(category=Expense.Category.SALARIES).aggregate(Sum("amount"))[
            "amount__sum"
        ]
        or 0
    )
    services = (
        qs.filter(category=Expense.Category.SERVICES).aggregate(Sum("amount"))[
            "amount__sum"
        ]
        or 0
    )

    return {
        "total_expenses": total,
        "total_factory": factory,
        "total_salaries": salaries,
        "total_services": services,
    }
