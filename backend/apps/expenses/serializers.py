from decimal import Decimal

from rest_framework import serializers

from apps.expenses.models import Expense
from apps.expenses.services import ExpenseService
from utils.serializers import BaseModelSerializer


class ExpenseSerializer(BaseModelSerializer):
    service_category_name = serializers.CharField(
        source="service_category.name",
        read_only=True,
    )

    class Meta:
        model = Expense
        fields = (
            "id",
            "amount",
            "description",
            "expense_date",
            "category",
            "service_category",
            "service_category_name",
            "created_at",
            "updated_at",
            "deleted_at",
            "created_by",
            "updated_by",
        )
        read_only_fields = (
            "id",
            "service_category_name",
            "created_at",
            "updated_at",
            "deleted_at",
            "created_by",
            "updated_by",
        )

    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_category(self, value: str) -> str:
        allowed = {choice.value for choice in Expense.Category}
        if value not in allowed:
            raise serializers.ValidationError("Invalid category.")
        return value

    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None))
        service_category = attrs.get(
            "service_category", getattr(self.instance, "service_category", None)
        )

        if category == Expense.Category.SERVICES:
            if not service_category:
                raise serializers.ValidationError(
                    {
                        "service_category": (
                            "Service Category is required when Category is Services."
                        )
                    }
                )
        else:
            # If not services, force service_category to None
            attrs["service_category"] = None

        return attrs

    def create(self, validated_data):
        validated_data = self.assign_audit_on_create(validated_data)
        return ExpenseService.create(
            amount=validated_data["amount"],
            description=validated_data["description"],
            expense_date=validated_data["expense_date"],
            category=validated_data["category"],
            service_category=validated_data.get("service_category"),
            created_by=validated_data.get("created_by"),
            updated_by=validated_data.get("updated_by"),
        )

    def update(self, instance, validated_data):
        validated_data = self.assign_audit_on_update(validated_data)
        return ExpenseService.update(
            expense=instance,
            amount=validated_data.get("amount", instance.amount),
            description=validated_data.get("description", instance.description),
            expense_date=validated_data.get("expense_date", instance.expense_date),
            category=validated_data.get("category", instance.category),
            service_category=validated_data.get(
                "service_category", instance.service_category
            ),
            updated_by=validated_data.get("updated_by"),
        )
