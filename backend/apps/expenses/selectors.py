from typing import Any

from django.db.models import QuerySet, Sum

from apps.expenses.filters import ExpenseFilter
from apps.expenses.models import (
    Expense,
    ExpenseCategory,
    ExpenseMainCategory,
)


def get_main_categories() -> QuerySet[ExpenseMainCategory]:
    return ExpenseMainCategory.objects.all()


def get_categories() -> QuerySet[ExpenseCategory]:
    return ExpenseCategory.objects.select_related("main_category").all()


def get_expenses(*, filters: dict[str, Any] | None = None) -> QuerySet[Expense]:
    filters = filters or {}
    qs = Expense.objects.select_related("category__main_category", "client").all()
    return ExpenseFilter(filters, qs).qs


def get_expenses_summary(*, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    qs = get_expenses(filters=filters)

    total = qs.aggregate(Sum("amount"))["amount__sum"] or 0
    rows = (
        qs.order_by()
        .values("category__main_category_id", "category__main_category__name")
        .annotate(total=Sum("amount"))
        .order_by("category__main_category__name")
    )
    by_main_category = [
        {
            "main_category": row["category__main_category_id"],
            "main_category_name": row["category__main_category__name"],
            "total": row["total"],
        }
        for row in rows
    ]

    return {"total_expenses": total, "by_main_category": by_main_category}
