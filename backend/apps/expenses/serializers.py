from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from apps.expenses.models import (
    Expense,
    ExpenseCategory,
    ExpenseMainCategory,
)
from apps.expenses.services import (
    ExpenseCategoryService,
    ExpenseMainCategoryService,
    ExpenseService,
)
from utils.serializers import BaseModelSerializer

AUDIT_FIELDS = (
    "created_at",
    "updated_at",
    "deleted_at",
    "created_by",
    "updated_by",
)


class ExpenseMainCategorySerializer(BaseModelSerializer):
    categories_count = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseMainCategory
        fields = ("id", "name", "categories_count", *AUDIT_FIELDS)
        read_only_fields = ("id", "categories_count", *AUDIT_FIELDS)

    def get_categories_count(self, obj: ExpenseMainCategory) -> int:
        return obj.categories.count()

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required.")
        qs = ExpenseMainCategory.objects.filter(name=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A main category with this name already exists."
            )
        return value

    def create(self, validated_data):
        validated_data = self.assign_audit_on_create(validated_data)
        return ExpenseMainCategoryService.create(
            name=validated_data["name"],
            created_by=validated_data.get("created_by"),
            updated_by=validated_data.get("updated_by"),
        )

    def update(self, instance, validated_data):
        validated_data = self.assign_audit_on_update(validated_data)
        return ExpenseMainCategoryService.update(
            category=instance,
            name=validated_data.get("name", instance.name),
            updated_by=validated_data.get("updated_by"),
        )


class ExpenseCategorySerializer(BaseModelSerializer):
    main_category_name = serializers.CharField(
        source="main_category.name", read_only=True
    )
    expenses_count = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseCategory
        fields = (
            "id",
            "main_category",
            "main_category_name",
            "name",
            "order_number",
            "is_shown",
            "expenses_count",
            *AUDIT_FIELDS,
        )
        read_only_fields = (
            "id",
            "main_category_name",
            "expenses_count",
            *AUDIT_FIELDS,
        )

    def get_expenses_count(self, obj: ExpenseCategory) -> int:
        count = getattr(obj, "expenses_count", None)
        return count if count is not None else obj.expenses.count()

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required.")
        return value

    def validate(self, attrs):
        main_category = attrs.get(
            "main_category", getattr(self.instance, "main_category", None)
        )
        name = attrs.get("name", getattr(self.instance, "name", None))
        qs = ExpenseCategory.objects.filter(main_category=main_category, name=name)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                {"name": "A category with this name already exists in this main category."}
            )
        return attrs

    def create(self, validated_data):
        validated_data = self.assign_audit_on_create(validated_data)
        return ExpenseCategoryService.create(
            main_category=validated_data["main_category"],
            name=validated_data["name"],
            order_number=validated_data.get("order_number", 0),
            is_shown=validated_data.get("is_shown", True),
            created_by=validated_data.get("created_by"),
            updated_by=validated_data.get("updated_by"),
        )

    def update(self, instance, validated_data):
        validated_data = self.assign_audit_on_update(validated_data)
        return ExpenseCategoryService.update(
            category=instance,
            main_category=validated_data.get("main_category", instance.main_category),
            name=validated_data.get("name", instance.name),
            order_number=validated_data.get("order_number", instance.order_number),
            is_shown=validated_data.get("is_shown", instance.is_shown),
            updated_by=validated_data.get("updated_by"),
        )


class ExpenseCategoryDetailSerializer(ExpenseCategorySerializer):
    total_amount = serializers.SerializerMethodField()
    last_expenses = serializers.SerializerMethodField()

    class Meta(ExpenseCategorySerializer.Meta):
        fields = (*ExpenseCategorySerializer.Meta.fields, "total_amount", "last_expenses")
        read_only_fields = (
            *ExpenseCategorySerializer.Meta.read_only_fields,
            "total_amount",
            "last_expenses",
        )

    def get_total_amount(self, obj: ExpenseCategory) -> Decimal:
        return obj.expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    def get_last_expenses(self, obj: ExpenseCategory) -> list[dict]:
        qs = obj.expenses.select_related("client").order_by("-expense_date", "-id")[:5]
        return [
            {
                "id": e.id,
                "amount": e.amount,
                "description": e.description,
                "expense_date": e.expense_date,
                "client_name": e.client.name if e.client else None,
            }
            for e in qs
        ]


class ExpenseSerializer(BaseModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    main_category = serializers.IntegerField(
        source="category.main_category_id", read_only=True
    )
    main_category_name = serializers.CharField(
        source="category.main_category.name", read_only=True
    )
    client_name = serializers.CharField(
        source="client.name", read_only=True, default=None
    )

    class Meta:
        model = Expense
        fields = (
            "id",
            "amount",
            "description",
            "expense_date",
            "category",
            "category_name",
            "main_category",
            "main_category_name",
            "client",
            "client_name",
            *AUDIT_FIELDS,
        )
        read_only_fields = (
            "id",
            "category_name",
            "main_category",
            "main_category_name",
            "client_name",
            *AUDIT_FIELDS,
        )

    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def create(self, validated_data):
        validated_data = self.assign_audit_on_create(validated_data)
        return ExpenseService.create(
            amount=validated_data["amount"],
            description=validated_data["description"],
            expense_date=validated_data["expense_date"],
            category=validated_data["category"],
            client=validated_data.get("client"),
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
            client=validated_data.get("client", instance.client),
            updated_by=validated_data.get("updated_by"),
        )
