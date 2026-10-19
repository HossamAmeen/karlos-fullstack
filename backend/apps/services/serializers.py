import re
from decimal import Decimal

from rest_framework import serializers

from apps.services.models import Service, ServiceCategory
from apps.services.services import UNSET, ServiceCategoryService, ServiceService
from utils.serializers import BaseModelSerializer


class ServiceCategorySerializer(BaseModelSerializer):
    icon = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = ServiceCategory
        fields = (
            "id",
            "name",
            "icon",
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

        qs = ServiceCategory.objects.filter(name=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A service category with this name already exists."
            )
        return value

    def create(self, validated_data):
        validated_data = self.assign_audit_on_create(validated_data)
        return ServiceCategoryService.create(
            name=validated_data["name"],
            icon=validated_data.get("icon"),
            created_by=validated_data.get("created_by"),
            updated_by=validated_data.get("updated_by"),
        )

    def update(self, instance, validated_data):
        validated_data = self.assign_audit_on_update(validated_data)
        return ServiceCategoryService.update(
            category=instance,
            name=validated_data.get("name", instance.name),
            icon=validated_data.get("icon", UNSET),
            updated_by=validated_data.get("updated_by"),
        )


class ServiceSerializer(BaseModelSerializer):
    icon = serializers.ImageField(required=False, allow_null=True)
    service_category_name = serializers.CharField(
        source="service_category.name",
        read_only=True,
    )

    class Meta:
        model = Service
        fields = (
            "id",
            "name",
            "service_category",
            "service_category_name",
            "cost",
            "cost_method",
            "is_fixed_cost",
            "is_additional_service",
            "color",
            "icon",
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

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required.")
        return value

    def validate_cost(self, value: Decimal) -> Decimal:
        if value < 0:
            raise serializers.ValidationError(
                "Cost must be greater than or equal to 0."
            )
        return value

    def validate_cost_method(self, value: str) -> str:
        allowed = {choice.value for choice in Service.CostMethod}
        if value not in allowed:
            raise serializers.ValidationError(
                "Cost method must be one of: fixed, quantity, one_dimension, "
                "two_dimensions."
            )
        return value

    def validate_service_category(self, value: ServiceCategory) -> ServiceCategory:
        # Soft-deleted categories are already excluded by the default manager.
        if value.deleted_at is not None:
            raise serializers.ValidationError(
                "Cannot assign a soft-deleted service category."
            )
        return value

    def validate_color(self, value: str) -> str:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise serializers.ValidationError(
                "Color must be a valid hex color code (e.g., #3b82f6)."
            )
        return value

    def create(self, validated_data):
        validated_data = self.assign_audit_on_create(validated_data)
        return ServiceService.create(
            name=validated_data["name"],
            service_category=validated_data["service_category"],
            cost=validated_data["cost"],
            cost_method=validated_data.get(
                "cost_method", Service.CostMethod.TWO_DIMENSIONS
            ),
            is_fixed_cost=validated_data.get("is_fixed_cost", False),
            is_additional_service=validated_data.get("is_additional_service", False),
            color=validated_data.get("color", "#3b82f6"),
            icon=validated_data.get("icon"),
            created_by=validated_data.get("created_by"),
            updated_by=validated_data.get("updated_by"),
        )

    def update(self, instance, validated_data):
        validated_data = self.assign_audit_on_update(validated_data)
        return ServiceService.update(
            service=instance,
            name=validated_data.get("name", instance.name),
            service_category=validated_data.get(
                "service_category", instance.service_category
            ),
            cost=validated_data.get("cost", instance.cost),
            cost_method=validated_data.get("cost_method", instance.cost_method),
            is_fixed_cost=validated_data.get("is_fixed_cost", instance.is_fixed_cost),
            is_additional_service=validated_data.get(
                "is_additional_service", instance.is_additional_service
            ),
            color=validated_data.get("color", instance.color),
            icon=validated_data.get("icon", UNSET),
            updated_by=validated_data.get("updated_by"),
        )
