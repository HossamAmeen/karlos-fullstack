from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.clients.models import Client
from apps.invoices.models import Invoice, InvoiceItem, InvoicePiece
from apps.invoices.services import InvoiceService
from apps.services.models import Service
from utils.serializers import BaseModelSerializer


def _django_to_drf(exc: DjangoValidationError) -> None:
    if hasattr(exc, "message_dict"):
        raise serializers.ValidationError(exc.message_dict) from exc
    raise serializers.ValidationError(exc.messages) from exc


class InvoiceItemSerializer(BaseModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = (
            "id",
            "piece",
            "service",
            "service_name",
            "service_color",
            "cost_method",
            "unit_price",
            "quantity",
            "length",
            "width",
            "measure",
            "discount_amount",
            "line_subtotal",
            "line_total",
            "position",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class InvoicePieceSerializer(BaseModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = InvoicePiece
        fields = (
            "id",
            "length",
            "width",
            "quantity",
            "notes",
            "piece_subtotal",
            "piece_total",
            "position",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class InvoiceSerializer(BaseModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    pieces = InvoicePieceSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True)
    amount_remaining = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "number",
            "client",
            "client_name",
            "issue_date",
            "status",
            "discount_amount",
            "notes",
            "subtotal",
            "total",
            "amount_paid",
            "amount_remaining",
            "payment_status",
            "is_settled",
            "confirmed_at",
            "cancelled_at",
            "pieces",
            "items",
            "created_at",
            "updated_at",
            "deleted_at",
            "created_by",
            "updated_by",
        )
        read_only_fields = (
            "id",
            "number",
            "client_name",
            "status",
            "subtotal",
            "total",
            "amount_paid",
            "amount_remaining",
            "payment_status",
            "is_settled",
            "confirmed_at",
            "cancelled_at",
            "pieces",
            "items",
            "created_at",
            "updated_at",
            "deleted_at",
            "created_by",
            "updated_by",
        )

    def validate_client(self, value: Client) -> Client:
        if value.deleted_at is not None:
            raise serializers.ValidationError("Cannot use a soft-deleted client.")
        return value

    def validate_discount_amount(self, value: Decimal) -> Decimal:
        if value < 0:
            raise serializers.ValidationError("Discount must be >= 0.")
        return value

    def create(self, validated_data):
        validated_data = self.assign_audit_on_create(validated_data)
        try:
            return InvoiceService.create_draft(
                client=validated_data["client"],
                discount_amount=validated_data.get("discount_amount", Decimal("0")),
                notes=validated_data.get("notes", ""),
                issue_date=validated_data.get("issue_date"),
                created_by=validated_data.get("created_by"),
                updated_by=validated_data.get("updated_by"),
            )
        except DjangoValidationError as exc:
            _django_to_drf(exc)

    def update(self, instance, validated_data):
        validated_data = self.assign_audit_on_update(validated_data)
        try:
            return InvoiceService.update_header(
                invoice=instance,
                client=validated_data.get("client"),
                discount_amount=validated_data.get("discount_amount"),
                notes=validated_data.get("notes"),
                issue_date=validated_data.get("issue_date"),
                updated_by=validated_data.get("updated_by"),
            )
        except DjangoValidationError as exc:
            _django_to_drf(exc)


class InvoiceItemWriteSerializer(serializers.Serializer):
    service: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all()
    )
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    length = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    width = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    measure = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    discount_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=Decimal("0")
    )
    piece: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        queryset=InvoicePiece.objects.all(),
        required=False,
        allow_null=True,
    )
    piece_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        required=False,
        allow_null=True,
        min_value=Decimal("0.001"),
    )

    def validate_discount_amount(self, value: Decimal) -> Decimal:
        if value < 0:
            raise serializers.ValidationError("Discount must be >= 0.")
        return value

    def validate_unit_price(self, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise serializers.ValidationError("Unit price must be >= 0.")
        return value


class InvoicePieceItemWriteSerializer(serializers.Serializer):
    service: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all()
    )
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    measure = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    discount_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=Decimal("0")
    )

    def validate_discount_amount(self, value: Decimal) -> Decimal:
        if value < 0:
            raise serializers.ValidationError("Discount must be >= 0.")
        return value

    def validate_unit_price(self, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise serializers.ValidationError("Unit price must be >= 0.")
        return value


class InvoicePieceWriteSerializer(serializers.Serializer):
    length = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    width = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        required=False,
        default=Decimal("1"),
        min_value=Decimal("0.001"),
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    items = InvoicePieceItemWriteSerializer(many=True)

    def validate_items(self, value: list) -> list:
        if not value:
            raise serializers.ValidationError("A piece requires at least one service.")
        return value


class InvoicePieceUpdateSerializer(serializers.Serializer):
    length = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    width = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        required=False,
        min_value=Decimal("0.001"),
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class InvoiceConfirmSerializer(serializers.Serializer):
    amount_paid = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal("0"),
    )


class InvoicePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    paid_at = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_amount(self, value: Decimal) -> Decimal:
        invoice = self.context.get("invoice")
        if invoice is not None and value > invoice.amount_remaining:
            raise serializers.ValidationError(
                f"Payment exceeds remaining balance ({invoice.amount_remaining})."
            )
        return value
