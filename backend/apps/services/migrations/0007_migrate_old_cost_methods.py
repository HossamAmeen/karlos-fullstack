from django.db import migrations


def migrate_cost_methods(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    InvoiceItem = apps.get_model("invoices", "InvoiceItem")

    Service.objects.filter(cost_method="perimeter").update(cost_method="two_dimensions")
    Service.objects.filter(cost_method="area").update(cost_method="one_dimension")

    InvoiceItem.objects.filter(cost_method="perimeter").update(
        cost_method="two_dimensions"
    )
    InvoiceItem.objects.filter(cost_method="area").update(cost_method="one_dimension")


def reverse_cost_methods(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    InvoiceItem = apps.get_model("invoices", "InvoiceItem")

    Service.objects.filter(cost_method="two_dimensions").update(cost_method="perimeter")
    Service.objects.filter(cost_method="one_dimension").update(cost_method="area")

    InvoiceItem.objects.filter(cost_method="two_dimensions").update(
        cost_method="perimeter"
    )
    InvoiceItem.objects.filter(cost_method="one_dimension").update(cost_method="area")


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0006_remove_service_default_length_and_more"),
        ("invoices", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(migrate_cost_methods, reverse_code=reverse_cost_methods),
    ]
