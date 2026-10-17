from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "expense_date",
        "category",
        "amount",
        "service_category",
        "created_at",
        "deleted_at",
    )
    list_filter = ("category", "expense_date", "service_category")
    search_fields = ("description",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
        "created_by",
        "updated_by",
    )
