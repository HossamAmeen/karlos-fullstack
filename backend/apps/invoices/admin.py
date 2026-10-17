from django.contrib import admin

from apps.invoices.models import (
    Invoice,
    InvoiceItem,
    InvoicePiece,
    InvoiceSequence,
    Payment,
)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = (
        "service_name",
        "cost_method",
        "line_subtotal",
        "line_total",
        "position",
    )


class InvoicePieceInline(admin.TabularInline):
    model = InvoicePiece
    extra = 0
    readonly_fields = ("piece_subtotal", "piece_total", "position")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "client",
        "issue_date",
        "status",
        "subtotal",
        "total",
        "amount_paid",
        "created_at",
    )
    list_filter = ("status", "issue_date")
    search_fields = ("number", "client__name", "client__phone")
    inlines = [InvoicePieceInline, InvoiceItemInline]
    readonly_fields = (
        "number",
        "subtotal",
        "total",
        "amount_paid",
        "confirmed_at",
        "cancelled_at",
    )


@admin.register(InvoicePiece)
class InvoicePieceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "invoice",
        "length",
        "width",
        "quantity",
        "piece_total",
        "position",
    )
    inlines = [InvoiceItemInline]
    readonly_fields = ("piece_subtotal", "piece_total", "position")


@admin.register(InvoiceSequence)
class InvoiceSequenceAdmin(admin.ModelAdmin):
    list_display = ("year", "last_value")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "invoice", "amount", "paid_at", "created_at")
    list_filter = ("paid_at",)
    search_fields = ("client__name", "client__phone", "invoice__number", "notes")
    readonly_fields = ("created_at", "updated_at")
