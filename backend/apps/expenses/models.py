from django.db import models

from apps.services.models import ServiceCategory
from utils.models import BaseModel


class Expense(BaseModel):
    class Category(models.TextChoices):
        FACTORY = "factory", "Factory"
        SALARIES = "salaries", "Salaries"
        SERVICES = "services", "Services"

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    expense_date = models.DateField()
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
    )
    service_category = models.ForeignKey(
        ServiceCategory,
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
