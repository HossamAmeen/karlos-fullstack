from django.db import models

from utils.models import BaseModel


class ServiceCategory(BaseModel):
    name = models.CharField(max_length=255)
    icon = models.ImageField(upload_to="service_categories/", null=True, blank=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Service category"
        verbose_name_plural = "Service categories"
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(deleted_at__isnull=True),
                name="services_servicecategory_name_active_uniq",
            )
        ]

    def __str__(self) -> str:
        return self.name


class Service(BaseModel):
    class CostMethod(models.TextChoices):
        FIXED = "fixed", "Fixed"
        QUANTITY = "quantity", "Quantity"
        ONE_DIMENSION = "one_dimension", "One Dimension"
        TWO_DIMENSIONS = "two_dimensions", "Two Dimensions"

    name = models.CharField(max_length=255)
    service_category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
    )
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    cost_method = models.CharField(
        max_length=20,
        choices=CostMethod.choices,
        default=CostMethod.TWO_DIMENSIONS,
    )
    is_fixed_cost = models.BooleanField(default=False)
    is_additional_service = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default="#3b82f6")
    icon = models.ImageField(upload_to="services/", null=True, blank=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self) -> str:
        return f"{self.name} ({self.service_category})"
