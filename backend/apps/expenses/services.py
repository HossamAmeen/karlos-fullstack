from datetime import date
from decimal import Decimal
from typing import Any

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.clients.models import Client
from apps.expenses.models import (
    Expense,
    ExpenseCategory,
    ExpenseMainCategory,
)


class ExpenseMainCategoryService:
    @staticmethod
    def create(
        *, name: str, created_by: Any = None, updated_by: Any = None
    ) -> ExpenseMainCategory:
        return ExpenseMainCategory.objects.create(
            name=name.strip(),
            created_by=created_by,
            updated_by=updated_by if updated_by is not None else created_by,
        )

    @staticmethod
    def update(
        *, category: ExpenseMainCategory, name: str, updated_by: Any = None
    ) -> ExpenseMainCategory:
        category.name = name.strip()
        if updated_by is not None:
            category.updated_by = updated_by
        category.save(update_fields=["name", "updated_by", "updated_at"])
        return category

    @staticmethod
    def delete(*, category: ExpenseMainCategory) -> None:
        if category.categories.exists():
            raise ValidationError("Cannot delete a main category that has categories.")
        category.delete()


class ExpenseCategoryService:
    @staticmethod
    def create(
        *,
        main_category: ExpenseMainCategory,
        name: str,
        created_by: Any = None,
        updated_by: Any = None,
    ) -> ExpenseCategory:
        return ExpenseCategory.objects.create(
            main_category=main_category,
            name=name.strip(),
            created_by=created_by,
            updated_by=updated_by if updated_by is not None else created_by,
        )

    @staticmethod
    def update(
        *,
        category: ExpenseCategory,
        main_category: ExpenseMainCategory,
        name: str,
        updated_by: Any = None,
    ) -> ExpenseCategory:
        category.main_category = main_category
        category.name = name.strip()
        if updated_by is not None:
            category.updated_by = updated_by
        category.save(
            update_fields=["main_category", "name", "updated_by", "updated_at"]
        )
        return category

    @staticmethod
    def delete(*, category: ExpenseCategory) -> None:
        if category.expenses.exists():
            raise ValidationError("Cannot delete a category that has expenses.")
        category.delete()


class ExpenseService:
    @staticmethod
    @transaction.atomic
    def create(
        *,
        amount: Decimal,
        description: str,
        expense_date: date,
        category: ExpenseCategory,
        client: Client | None = None,
        created_by: Any = None,
        updated_by: Any = None,
    ) -> Expense:
        expense = Expense(
            amount=amount,
            description=description,
            expense_date=expense_date,
            category=category,
            client=client,
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
        category: ExpenseCategory,
        client: Client | None = None,
        updated_by: Any = None,
    ) -> Expense:
        expense.amount = amount
        expense.description = description
        expense.expense_date = expense_date
        expense.category = category
        expense.client = client
        if updated_by is not None:
            expense.updated_by = updated_by

        expense.full_clean()
        expense.save(
            update_fields=[
                "amount",
                "description",
                "expense_date",
                "category",
                "client",
                "updated_by",
                "updated_at",
            ]
        )
        return expense
