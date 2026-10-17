from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_pieces(apps, schema_editor):
    InvoiceItem = apps.get_model("invoices", "InvoiceItem")
    InvoicePiece = apps.get_model("invoices", "InvoicePiece")
    items = InvoiceItem.objects.all().order_by("invoice_id", "position", "id")
    for item in items:
        piece = InvoicePiece.objects.create(
            invoice_id=item.invoice_id,
            length=item.length,
            width=item.width,
            quantity=Decimal("1"),
            notes="",
            piece_subtotal=item.line_total,
            piece_total=item.line_total,
            position=item.position,
            created_at=item.created_at,
            updated_at=item.updated_at,
            deleted_at=item.deleted_at,
            created_by_id=item.created_by_id,
            updated_by_id=item.updated_by_id,
        )
        item.piece_id = piece.id
        item.save(update_fields=["piece_id"])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("invoices", "0004_invoice_is_settled"),
    ]

    operations = [
        migrations.CreateModel(
            name="InvoicePiece",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "length",
                    models.DecimalField(
                        blank=True, decimal_places=3, max_digits=12, null=True
                    ),
                ),
                (
                    "width",
                    models.DecimalField(
                        blank=True, decimal_places=3, max_digits=12, null=True
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=3,
                        default=Decimal("1"),
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("notes", models.CharField(blank=True, default="", max_length=255)),
                (
                    "piece_subtotal",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                (
                    "piece_total",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                ("position", models.PositiveIntegerField(default=1)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pieces",
                        to="invoices.invoice",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Invoice piece",
                "verbose_name_plural": "Invoice pieces",
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddField(
            model_name="invoiceitem",
            name="piece",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="invoices.invoicepiece",
            ),
        ),
        migrations.RunPython(backfill_pieces, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="invoiceitem",
            name="piece",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="invoices.invoicepiece",
            ),
        ),
    ]
