from datetime import date
from decimal import Decimal
from typing import Any

from django.db import transaction

from apps.expenses.models import Expense
from apps.services.models import ServiceCategory


class ExpenseService:
    @staticmethod
    @transaction.atomic
    def create(
        *,
        amount: Decimal,
        description: str,
        expense_date: date,
        category: str,
        service_category: ServiceCategory | None = None,
        created_by: Any = None,
        updated_by: Any = None,
    ) -> Expense:
        expense = Expense(
            amount=amount,
            description=description,
            expense_date=expense_date,
            category=category,
            service_category=service_category,
            created_by=created_by,
            updated_by=updated_by,
        )
        expense.full_clean()
        expense.save()
        return expense

    @staticmethod
    @transaction.atomic
    def update(
        *,
        expense: Expense,
        amount: Decimal,
        description: str,
        expense_date: date,
        category: str,
        service_category: ServiceCategory | None = None,
        updated_by: Any = None,
    ) -> Expense:
        expense.amount = amount
        expense.description = description
        expense.expense_date = expense_date
        expense.category = category
        expense.service_category = service_category
        if updated_by is not None:
            expense.updated_by = updated_by

        expense.full_clean()
        expense.save(
            update_fields=[
                "amount",
                "description",
                "expense_date",
                "category",
                "service_category",
                "updated_by",
                "updated_at",
            ]
        )
        return expense
