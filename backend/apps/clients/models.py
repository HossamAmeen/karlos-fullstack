from django.db import models

from utils.models import BaseModel


class Client(BaseModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        constraints = [
            models.UniqueConstraint(
                fields=["phone"],
                condition=models.Q(deleted_at__isnull=True),
                name="clients_client_phone_active_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"
