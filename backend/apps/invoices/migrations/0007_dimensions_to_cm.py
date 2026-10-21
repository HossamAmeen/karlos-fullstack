from django.db import migrations
from django.db.models import F


def meters_to_cm(apps, schema_editor):
    for name in ("InvoicePiece", "InvoiceItem"):
        model = apps.get_model("invoices", name)
        model.objects.filter(length__isnull=False).update(length=F("length") * 100)
        model.objects.filter(width__isnull=False).update(width=F("width") * 100)


def cm_to_meters(apps, schema_editor):
    for name in ("InvoicePiece", "InvoiceItem"):
        model = apps.get_model("invoices", name)
        model.objects.filter(length__isnull=False).update(length=F("length") / 100)
        model.objects.filter(width__isnull=False).update(width=F("width") / 100)


class Migration(migrations.Migration):
    """Piece / item length and width were stored in metres; they are now cm."""

    dependencies = [
        ("invoices", "0006_invoiceitem_measure"),
    ]

    operations = [
        migrations.RunPython(meters_to_cm, cm_to_meters),
    ]
