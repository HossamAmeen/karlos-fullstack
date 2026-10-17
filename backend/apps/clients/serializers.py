from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.clients.models import Client
from apps.clients.services import ClientService
from apps.invoices.models import Invoice, Payment
from utils.serializers import BaseModelSerializer


def _django_to_drf(exc: DjangoValidationError) -> None:
    if hasattr(exc, "message_dict"):
        raise serializers.ValidationError(exc.message_dict) from exc
    raise serializers.ValidationError(exc.messages) from exc


class ClientSerializer(BaseModelSerializer):
    class Meta:
        model = Client
        fields = (
            "id",
            "name",
            "phone",
            "email",
            "address",
            "note",
            "created_at",
            "updated_at",
            "deleted_at",
            "created_by",
            "updated_by",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
            "created_by",
            "updated_by",
        )

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required.")
        return value

    def validate_phone(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone is required.")

        qs = Client.objects.filter(phone=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A client with this phone already exists."
            )
        return value

    def create(self, validated_data):
        validated_data = self.assign_audit_on_create(validated_data)
        return ClientService.create(
            name=validated_data["name"],
            phone=validated_data["phone"],
            email=validated_data.get("email"),
            address=validated_data.get("address"),
            note=validated_data.get("note"),
            created_by=validated_data.get("created_by"),
            updated_by=validated_data.get("updated_by"),
        )

    def update(self, instance, validated_data):
        validated_data = self.assign_audit_on_update(validated_data)
        return ClientService.update(
            client=instance,
            name=validated_data.get("name", instance.name),
            phone=validated_data.get("phone", instance.phone),
            email=validated_data.get("email", instance.email),
            address=validated_data.get("address", instance.address),
            note=validated_data.get("note", instance.note),
            updated_by=validated_data.get("updated_by"),
        )


class ClientDepositWriteSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    paid_at = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ClientStatementInvoiceSerializer(serializers.ModelSerializer):
    amount_remaining = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "number",
            "issue_date",
            "status",
            "total",
            "amount_paid",
            "amount_remaining",
            "payment_status",
        )


class ClientStatementDepositSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(
        source="invoice.number", read_only=True, allow_null=True
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "amount",
            "paid_at",
            "notes",
            "invoice",
            "invoice_number",
            "created_at",
        )


class ClientStatementSerializer(serializers.Serializer):
    client = ClientSerializer()
    total_charged = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_deposits = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2)
    invoices = ClientStatementInvoiceSerializer(many=True)
    deposits = ClientStatementDepositSerializer(many=True)
