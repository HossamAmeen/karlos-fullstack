from django.db import models

from apps.clients.models import Client
from utils.models import BaseModel


class ExpenseMainCategory(BaseModel):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Expense main category"
        verbose_name_plural = "Expense main categories"
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(deleted_at__isnull=True),
                name="expenses_mainctg_name_active_uniq",
            )
        ]

    def __str__(self) -> str:
        return self.name


class ExpenseCategory(BaseModel):
    main_category = models.ForeignKey(
        ExpenseMainCategory,
        on_delete=models.PROTECT,
        related_name="categories",
    )
    name = models.CharField(max_length=255)
    order_number = models.PositiveIntegerField(default=0)
    is_shown = models.BooleanField(default=True)

    class Meta:
        ordering = ["main_category__name", "order_number", "name", "id"]
        verbose_name = "Expense category"
        verbose_name_plural = "Expense categories"
        constraints = [
            models.UniqueConstraint(
                fields=["main_category", "name"],
                condition=models.Q(deleted_at__isnull=True),
                name="expenses_category_name_active_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.main_category} / {self.name}"


class Expense(BaseModel):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    expense_date = models.DateField()
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="expenses",
    )

    class Meta:
        ordering = ["-expense_date", "-id"]
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"

    def __str__(self) -> str:
        return f"{self.category} - {self.amount} ({self.expense_date})"
