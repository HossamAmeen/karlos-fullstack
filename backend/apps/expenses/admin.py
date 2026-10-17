from django.contrib import admin

from .models import Expense, ExpenseCategory, ExpenseMainCategory

AUDIT_READONLY = (
    "created_at",
    "updated_at",
    "deleted_at",
    "created_by",
    "updated_by",
)


@admin.register(ExpenseMainCategory)
class ExpenseMainCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "deleted_at")
    search_fields = ("name",)
    readonly_fields = AUDIT_READONLY


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "main_category", "created_at", "deleted_at")
    list_filter = ("main_category",)
    search_fields = ("name",)
    readonly_fields = AUDIT_READONLY


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "expense_date",
        "category",
        "amount",
        "client",
        "created_at",
        "deleted_at",
    )
    list_filter = ("category__main_category", "category", "expense_date")
    search_fields = ("description",)
    readonly_fields = AUDIT_READONLY
