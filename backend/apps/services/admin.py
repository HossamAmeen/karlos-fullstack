from django.contrib import admin

from apps.services.models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("name",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
        "created_by",
        "updated_by",
    )
    ordering = ("name", "id")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "service_category",
        "cost",
        "cost_method",
        "is_fixed_cost",
        "is_additional_service",
        "color",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "cost_method",
        "is_fixed_cost",
        "is_additional_service",
        "service_category",
        "created_at",
    )
    search_fields = ("name", "service_category__name")
    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
        "created_by",
        "updated_by",
    )
    ordering = ("name", "id")
