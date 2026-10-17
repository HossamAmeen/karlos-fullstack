from django.contrib import admin

from apps.clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "email", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("name", "phone", "email", "address", "note")
    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
        "created_by",
        "updated_by",
    )
    ordering = ("name", "id")
