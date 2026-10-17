from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.services.models import Service
from utils.models import BaseModel


class InvoiceSequence(models.Model):
    """Per-year counter for invoice numbers (locked with select_for_update)."""

    year = models.PositiveIntegerField(unique=True)
    last_value = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Invoice sequence"
        verbose_name_plural = "Invoice sequences"

    def __str__(self) -> str:
        return f"{self.year}:{self.last_value}"


class Invoice(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    number = models.CharField(max_length=32, unique=True)
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    issue_date = models.DateField(default=timezone.localdate)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    notes = models.TextField(blank=True, default="")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    is_settled = models.BooleanField(default=False, db_index=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-issue_date", "-id"]
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def __str__(self) -> str:
        return f"{self.number} ({self.status})"

    @property
    def is_editable(self) -> bool:
        return self.status == self.Status.DRAFT

    @property
    def amount_remaining(self) -> Decimal:
        remaining = self.total - self.amount_paid
        return remaining if remaining > 0 else Decimal("0")

    @property
    def payment_status(self) -> str:
        if self.amount_paid <= 0:
            return "unpaid"
        if self.amount_paid >= self.total:
            return "paid"
        return "partial"


class Payment(BaseModel):
    """Money received from a client (deposit), optionally linked to an invoice."""

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    paid_at = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-paid_at", "-id"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self) -> str:
        target = self.invoice.number if self.invoice is not None else "deposit"
        return f"{self.amount} → {self.client_id} ({target})"


class InvoicePiece(BaseModel):
    """One physical item (e.g. glass 3×2) that can carry multiple services."""

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="pieces",
    )
    length = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )
    width = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("1"),
        validators=[MinValueValidator(0)],
    )
    notes = models.CharField(max_length=255, blank=True, default="")
    piece_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    piece_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "Invoice piece"
        verbose_name_plural = "Invoice pieces"

    def __str__(self) -> str:
        size = ""
        if self.length is not None and self.width is not None:
            size = f" {self.length}×{self.width}"
        return f"Piece{size} @ {self.invoice.number}"


class InvoiceItem(BaseModel):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    piece = models.ForeignKey(
        InvoicePiece,
        on_delete=models.CASCADE,
        related_name="items",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="invoice_items",
    )
    service_name = models.CharField(max_length=255)
    service_color = models.CharField(max_length=7, default="#3b82f6")
    cost_method = models.CharField(max_length=20, choices=Service.CostMethod.choices)
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )
    length = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )
    width = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    line_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "Invoice item"
        verbose_name_plural = "Invoice items"

    def __str__(self) -> str:
        return f"{self.service_name} @ {self.invoice.number}"
