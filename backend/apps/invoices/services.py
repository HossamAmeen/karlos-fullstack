from __future__ import annotations

from decimal import Decimal
from typing import cast

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.clients.models import Client
from apps.invoices.models import (
    Invoice,
    InvoiceItem,
    InvoicePiece,
    InvoiceSequence,
    Payment,
)
from apps.services.models import Service
from apps.services.pricing import apply_discount, compute_line_subtotal, quantize_money


class PaymentService:
    @staticmethod
    @transaction.atomic
    def record(
        *,
        client: Client,
        amount: Decimal,
        invoice: Invoice | None = None,
        paid_at=None,
        notes: str = "",
        created_by: AbstractBaseUser | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Payment:
        amount = quantize_money(amount)
        if amount <= 0:
            raise ValidationError({"amount": "Payment amount must be > 0."})
        if client.deleted_at is not None:
            raise ValidationError({"client": "Cannot use a soft-deleted client."})

        locked_invoice: Invoice | None = None
        if invoice is not None:
            locked_invoice = cast(
                Invoice,
                Invoice.objects.select_for_update().get(pk=invoice.pk),
            )
            if locked_invoice.client_id != client.pk:
                raise ValidationError(
                    {"invoice": "Invoice does not belong to this client."}
                )
            if locked_invoice.status != Invoice.Status.CONFIRMED:
                raise ValidationError(
                    {"invoice": "Payments are allowed only on confirmed invoices."}
                )
            remaining = locked_invoice.amount_remaining
            if amount > remaining:
                raise ValidationError(
                    {"amount": (f"Payment exceeds remaining balance ({remaining}).")}
                )

        payment = Payment.objects.create(
            client=client,
            invoice=locked_invoice,
            amount=amount,
            paid_at=paid_at or timezone.localdate(),
            notes=notes or "",
            created_by=created_by,
            updated_by=updated_by if updated_by is not None else created_by,
        )

        if locked_invoice is not None:
            locked_invoice.amount_paid = quantize_money(
                locked_invoice.amount_paid + amount
            )
            locked_invoice.is_settled = (
                locked_invoice.amount_paid >= locked_invoice.total
            )
            update_fields = ["amount_paid", "is_settled", "updated_at"]
            if updated_by is not None:
                locked_invoice.updated_by = updated_by  # type: ignore[assignment]
                update_fields.append("updated_by")
            locked_invoice.save(update_fields=update_fields)

        return payment


class InvoiceService:
    @staticmethod
    def _allocate_number(*, year: int | None = None) -> str:
        year = year or timezone.localdate().year
        sequence, _ = InvoiceSequence.objects.select_for_update().get_or_create(
            year=year,
            defaults={"last_value": 0},
        )
        sequence.last_value += 1
        sequence.save(update_fields=["last_value"])
        return f"INV-{year}-{sequence.last_value:05d}"

    @staticmethod
    def _ensure_draft(invoice: Invoice) -> None:
        if invoice.status != Invoice.Status.DRAFT:
            raise ValidationError({"status": "Only draft invoices can be modified."})

    @staticmethod
    def _needs_dimensions(cost_method: str) -> bool:
        return cost_method in (
            Service.CostMethod.ONE_DIMENSION,
            Service.CostMethod.TWO_DIMENSIONS,
        )

    @staticmethod
    def _recalculate_piece(piece: InvoicePiece) -> InvoicePiece:
        items = list(piece.items.all())
        subtotal = quantize_money(
            sum((item.line_total for item in items), Decimal("0"))
        )
        quantity = piece.quantity if piece.quantity is not None else Decimal("1")
        if quantity <= 0:
            raise ValidationError(
                {"quantity": "Piece quantity must be greater than 0."}
            )
        piece.piece_subtotal = subtotal
        piece.piece_total = quantize_money(subtotal * quantity)
        piece.save(update_fields=["piece_subtotal", "piece_total", "updated_at"])
        return piece

    @staticmethod
    def _recalculate_locked(invoice: Invoice) -> Invoice:
        pieces = list(invoice.pieces.all())
        for piece in pieces:
            InvoiceService._recalculate_piece(piece)
        subtotal = quantize_money(
            sum((piece.piece_total for piece in pieces), Decimal("0"))
        )
        total = apply_discount(
            amount=subtotal,
            discount=invoice.discount_amount,
            field="discount_amount",
        )
        invoice.subtotal = subtotal
        invoice.total = total
        invoice.is_settled = invoice.amount_paid >= total
        invoice.save(update_fields=["subtotal", "total", "is_settled", "updated_at"])
        return invoice

    @staticmethod
    def _next_piece_position(invoice: Invoice) -> int:
        current = invoice.pieces.aggregate(m=Max("position"))["m"]
        return int(current or 0) + 1

    @staticmethod
    def _next_item_position(piece: InvoicePiece) -> int:
        current = piece.items.aggregate(m=Max("position"))["m"]
        return int(current or 0) + 1

    @staticmethod
    def _build_item_amounts(
        *,
        cost_method: str,
        unit_price: Decimal,
        quantity: Decimal | None,
        length: Decimal | None,
        width: Decimal | None,
        discount_amount: Decimal,
    ) -> tuple[Decimal, Decimal]:
        line_subtotal = compute_line_subtotal(
            cost_method=cost_method,
            unit_price=unit_price,
            quantity=quantity,
            length=length,
            width=width,
        )
        line_total = apply_discount(
            amount=line_subtotal,
            discount=discount_amount,
            field="discount_amount",
        )
        return line_subtotal, line_total

    @staticmethod
    def _apply_item_amounts(
        *,
        item: InvoiceItem,
        piece: InvoicePiece,
        unit_price: Decimal,
        quantity: Decimal | None,
        discount_amount: Decimal,
        updated_by: AbstractBaseUser | None = None,
    ) -> InvoiceItem:
        if item.cost_method in (Service.CostMethod.ONE_DIMENSION, "area"):
            w = piece.width if piece.width is not None else piece.length
            if w is None:
                raise ValidationError(
                    {"width": "Width is required for one dimension cost method."}
                )
            length = None
            width = w
        elif item.cost_method in (Service.CostMethod.TWO_DIMENSIONS, "perimeter"):
            if piece.length is None or piece.width is None:
                raise ValidationError(
                    {
                        "length": (
                            "Length and width are required for two dimensions cost "
                            "method."
                        ),
                        "width": (
                            "Length and width are required for two dimensions cost "
                            "method."
                        ),
                    }
                )
            length = piece.length
            width = piece.width
        else:
            length = None
            width = None

        line_subtotal, line_total = InvoiceService._build_item_amounts(
            cost_method=item.cost_method,
            unit_price=unit_price,
            quantity=quantity,
            length=length,
            width=width,
            discount_amount=discount_amount,
        )
        item.unit_price = unit_price
        item.quantity = quantity
        item.length = length
        item.width = width
        item.discount_amount = discount_amount
        item.line_subtotal = line_subtotal
        item.line_total = line_total
        update_fields = [
            "unit_price",
            "quantity",
            "length",
            "width",
            "discount_amount",
            "line_subtotal",
            "line_total",
            "updated_at",
        ]
        if updated_by is not None:
            item.updated_by = updated_by  # type: ignore[assignment]
            update_fields.append("updated_by")
        item.save(update_fields=update_fields)
        return item

    @staticmethod
    def _recalculate_piece_items(piece: InvoicePiece) -> None:
        for item in piece.items.all():
            InvoiceService._apply_item_amounts(
                item=item,
                piece=piece,
                unit_price=item.unit_price,
                quantity=item.quantity,
                discount_amount=item.discount_amount,
            )

    @staticmethod
    def _create_item_on_piece(
        *,
        invoice: Invoice,
        piece: InvoicePiece,
        service: Service,
        unit_price: Decimal | None,
        quantity: Decimal | None,
        discount_amount: Decimal,
        created_by: AbstractBaseUser | None,
        updated_by: AbstractBaseUser | None,
    ) -> InvoiceItem:
        if service.deleted_at is not None:
            raise ValidationError({"service": "Cannot use a soft-deleted service."})

        price = quantize_money(service.cost if unit_price is None else unit_price)
        cost_method = service.cost_method
        if cost_method in (Service.CostMethod.ONE_DIMENSION, "area"):
            w = piece.width if piece.width is not None else piece.length
            if w is None:
                raise ValidationError(
                    {"width": "Width is required for one dimension cost method."}
                )
            length = None
            width = w
        elif cost_method in (Service.CostMethod.TWO_DIMENSIONS, "perimeter"):
            if piece.length is None or piece.width is None:
                raise ValidationError(
                    {
                        "length": (
                            "Length and width are required for two dimensions cost "
                            "method."
                        ),
                        "width": (
                            "Length and width are required for two dimensions cost "
                            "method."
                        ),
                    }
                )
            length = piece.length
            width = piece.width
        else:
            length = None
            width = None

        line_subtotal, line_total = InvoiceService._build_item_amounts(
            cost_method=cost_method,
            unit_price=price,
            quantity=quantity,
            length=length,
            width=width,
            discount_amount=quantize_money(discount_amount),
        )
        return InvoiceItem.objects.create(
            invoice=invoice,
            piece=piece,
            service=service,
            service_name=service.name,
            service_color=service.color,
            cost_method=cost_method,
            unit_price=price,
            quantity=quantity,
            length=length,
            width=width,
            discount_amount=quantize_money(discount_amount),
            line_subtotal=line_subtotal,
            line_total=line_total,
            position=InvoiceService._next_item_position(piece),
            created_by=created_by,
            updated_by=updated_by if updated_by is not None else created_by,
        )

    @staticmethod
    def _create_piece(
        *,
        invoice: Invoice,
        length: Decimal | None,
        width: Decimal | None,
        quantity: Decimal,
        notes: str,
        created_by: AbstractBaseUser | None,
        updated_by: AbstractBaseUser | None,
    ) -> InvoicePiece:
        qty = quantity if quantity is not None else Decimal("1")
        if qty <= 0:
            raise ValidationError(
                {"quantity": "Piece quantity must be greater than 0."}
            )
        if (length is not None and length < 0) or (width is not None and width < 0):
            raise ValidationError(
                {
                    "length": "Length and width must be >= 0.",
                    "width": "Length and width must be >= 0.",
                }
            )
        return InvoicePiece.objects.create(
            invoice=invoice,
            length=length,
            width=width,
            quantity=qty,
            notes=(notes or "").strip(),
            piece_subtotal=Decimal("0.00"),
            piece_total=Decimal("0.00"),
            position=InvoiceService._next_piece_position(invoice),
            created_by=created_by,
            updated_by=updated_by if updated_by is not None else created_by,
        )

    @staticmethod
    @transaction.atomic
    def create_draft(
        *,
        client: Client,
        discount_amount: Decimal = Decimal("0"),
        notes: str = "",
        issue_date=None,
        created_by: AbstractBaseUser | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Invoice:
        if discount_amount < 0:
            raise ValidationError({"discount_amount": "Discount must be >= 0."})
        if client.deleted_at is not None:
            raise ValidationError({"client": "Cannot use a soft-deleted client."})

        number = InvoiceService._allocate_number()
        return Invoice.objects.create(
            number=number,
            client=client,
            issue_date=issue_date or timezone.localdate(),
            status=Invoice.Status.DRAFT,
            discount_amount=quantize_money(discount_amount),
            notes=(notes or "").strip(),
            subtotal=Decimal("0.00"),
            total=Decimal("0.00"),
            created_by=created_by,
            updated_by=updated_by if updated_by is not None else created_by,
        )

    @staticmethod
    @transaction.atomic
    def update_header(
        *,
        invoice: Invoice,
        client: Client | None = None,
        discount_amount: Decimal | None = None,
        notes: str | None = None,
        issue_date=None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Invoice:
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        InvoiceService._ensure_draft(invoice)

        if client is not None:
            if client.deleted_at is not None:
                raise ValidationError({"client": "Cannot use a soft-deleted client."})
            invoice.client = client
        if discount_amount is not None:
            if discount_amount < 0:
                raise ValidationError({"discount_amount": "Discount must be >= 0."})
            invoice.discount_amount = quantize_money(discount_amount)
        if notes is not None:
            invoice.notes = notes.strip()
        if issue_date is not None:
            invoice.issue_date = issue_date
        if updated_by is not None:
            invoice.updated_by = updated_by  # type: ignore[assignment]

        invoice.save()
        return InvoiceService._recalculate_locked(invoice)

    @staticmethod
    @transaction.atomic
    def add_piece(
        *,
        invoice: Invoice,
        items: list[dict],
        length: Decimal | None = None,
        width: Decimal | None = None,
        quantity: Decimal = Decimal("1"),
        notes: str = "",
        created_by: AbstractBaseUser | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Invoice:
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        InvoiceService._ensure_draft(invoice)
        if not items:
            raise ValidationError({"items": "A piece requires at least one service."})

        piece = InvoiceService._create_piece(
            invoice=invoice,
            length=length,
            width=width,
            quantity=quantity,
            notes=notes,
            created_by=created_by,
            updated_by=updated_by,
        )
        for payload in items:
            InvoiceService._create_item_on_piece(
                invoice=invoice,
                piece=piece,
                service=payload["service"],
                unit_price=payload.get("unit_price"),
                quantity=payload.get("quantity"),
                discount_amount=payload.get("discount_amount", Decimal("0")),
                created_by=created_by,
                updated_by=updated_by,
            )
        return InvoiceService._recalculate_locked(invoice)

    @staticmethod
    @transaction.atomic
    def update_piece(
        *,
        invoice: Invoice,
        piece: InvoicePiece,
        length: Decimal | None = None,
        width: Decimal | None = None,
        quantity: Decimal | None = None,
        notes: str | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Invoice:
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        InvoiceService._ensure_draft(invoice)
        piece = InvoicePiece.objects.select_for_update().get(
            pk=piece.pk, invoice=invoice
        )

        if length is not None or width is not None:
            new_length = piece.length if length is None else length
            new_width = piece.width if width is None else width
            if (new_length is not None and new_length < 0) or (
                new_width is not None and new_width < 0
            ):
                raise ValidationError(
                    {
                        "length": "Length and width must be >= 0.",
                        "width": "Length and width must be >= 0.",
                    }
                )
            piece.length = new_length
            piece.width = new_width
        if quantity is not None:
            if quantity <= 0:
                raise ValidationError(
                    {"quantity": "Piece quantity must be greater than 0."}
                )
            piece.quantity = quantity
        if notes is not None:
            piece.notes = notes.strip()
        if updated_by is not None:
            piece.updated_by = updated_by  # type: ignore[assignment]
        piece.save()
        InvoiceService._recalculate_piece_items(piece)
        return InvoiceService._recalculate_locked(invoice)

    @staticmethod
    @transaction.atomic
    def remove_piece(*, invoice: Invoice, piece: InvoicePiece) -> Invoice:
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        InvoiceService._ensure_draft(invoice)
        piece = InvoicePiece.objects.select_for_update().get(
            pk=piece.pk, invoice=invoice
        )
        for item in piece.items.all():
            item.delete()
        piece.delete()
        return InvoiceService._recalculate_locked(invoice)

    @staticmethod
    @transaction.atomic
    def add_item(
        *,
        invoice: Invoice,
        service: Service,
        unit_price: Decimal | None = None,
        quantity: Decimal | None = None,
        length: Decimal | None = None,
        width: Decimal | None = None,
        discount_amount: Decimal = Decimal("0"),
        piece: InvoicePiece | None = None,
        piece_quantity: Decimal | None = None,
        created_by: AbstractBaseUser | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Invoice:
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        InvoiceService._ensure_draft(invoice)

        if piece is not None:
            try:
                piece = cast(
                    InvoicePiece,
                    InvoicePiece.objects.select_for_update().get(
                        pk=piece.pk, invoice=invoice
                    ),
                )
            except InvoicePiece.DoesNotExist as exc:
                raise ValidationError(
                    {"piece": "Piece not found on this invoice."}
                ) from exc
            if length is not None or width is not None:
                if length is not None:
                    piece.length = length
                if width is not None:
                    piece.width = width
                piece.save(update_fields=["length", "width", "updated_at"])
        else:
            piece = InvoiceService._create_piece(
                invoice=invoice,
                length=length,
                width=width,
                quantity=(
                    piece_quantity if piece_quantity is not None else Decimal("1")
                ),
                notes="",
                created_by=created_by,
                updated_by=updated_by,
            )

        InvoiceService._create_item_on_piece(
            invoice=invoice,
            piece=piece,
            service=service,
            unit_price=unit_price,
            quantity=quantity,
            discount_amount=discount_amount,
            created_by=created_by,
            updated_by=updated_by,
        )
        return InvoiceService._recalculate_locked(invoice)

    @staticmethod
    @transaction.atomic
    def update_item(
        *,
        invoice: Invoice,
        item: InvoiceItem,
        unit_price: Decimal | None = None,
        quantity: Decimal | None = None,
        length: Decimal | None = None,
        width: Decimal | None = None,
        discount_amount: Decimal | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Invoice:
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        InvoiceService._ensure_draft(invoice)
        item = InvoiceItem.objects.select_for_update().get(pk=item.pk, invoice=invoice)
        piece = InvoicePiece.objects.select_for_update().get(pk=item.piece_id)

        if length is not None or width is not None:
            new_length = piece.length if length is None else length
            new_width = piece.width if width is None else width
            if (new_length is not None and new_length < 0) or (
                new_width is not None and new_width < 0
            ):
                raise ValidationError(
                    {
                        "length": "Length and width must be >= 0.",
                        "width": "Length and width must be >= 0.",
                    }
                )
            piece.length = new_length
            piece.width = new_width
            piece.save(update_fields=["length", "width", "updated_at"])
            InvoiceService._recalculate_piece_items(piece)
            item.refresh_from_db()

        price = item.unit_price if unit_price is None else quantize_money(unit_price)
        qty = item.quantity if quantity is None else quantity
        disc = (
            item.discount_amount
            if discount_amount is None
            else quantize_money(discount_amount)
        )
        InvoiceService._apply_item_amounts(
            item=item,
            piece=piece,
            unit_price=price,
            quantity=qty,
            discount_amount=disc,
            updated_by=updated_by,
        )
        return InvoiceService._recalculate_locked(invoice)

    @staticmethod
    @transaction.atomic
    def remove_item(
        *,
        invoice: Invoice,
        item: InvoiceItem,
    ) -> Invoice:
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        InvoiceService._ensure_draft(invoice)
        item = InvoiceItem.objects.select_for_update().get(pk=item.pk, invoice=invoice)
        piece = item.piece
        item.delete()
        if not piece.items.exists():
            piece.delete()
        return InvoiceService._recalculate_locked(invoice)

    @staticmethod
    @transaction.atomic
    def confirm(
        *,
        invoice: Invoice,
        amount_paid: Decimal | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Invoice:
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        InvoiceService._ensure_draft(invoice)
        if not invoice.items.exists():
            raise ValidationError(
                {"items": "Confirm requires at least one invoice item."}
            )
        InvoiceService._recalculate_locked(invoice)
        invoice.status = Invoice.Status.CONFIRMED
        invoice.confirmed_at = timezone.now()
        if updated_by is not None:
            invoice.updated_by = updated_by  # type: ignore[assignment]
        invoice.save(
            update_fields=["status", "confirmed_at", "updated_by", "updated_at"]
        )

        if amount_paid is not None and amount_paid > 0:
            PaymentService.record(
                client=invoice.client,
                invoice=invoice,
                amount=amount_paid,
                created_by=updated_by,
                updated_by=updated_by,
            )
            invoice.refresh_from_db()

        return invoice

    @staticmethod
    @transaction.atomic
    def record_payment(
        *,
        invoice: Invoice,
        amount: Decimal,
        paid_at=None,
        notes: str = "",
        created_by: AbstractBaseUser | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Invoice:
        PaymentService.record(
            client=invoice.client,
            invoice=invoice,
            amount=amount,
            paid_at=paid_at,
            notes=notes,
            created_by=created_by,
            updated_by=updated_by,
        )
        return (
            Invoice.objects.select_related("client")
            .prefetch_related("pieces", "items")
            .get(pk=invoice.pk)
        )

    @staticmethod
    @transaction.atomic
    def cancel(
        *,
        invoice: Invoice,
        updated_by: AbstractBaseUser | None = None,
    ) -> Invoice:
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        if invoice.status == Invoice.Status.CANCELLED:
            raise ValidationError({"status": "Invoice is already cancelled."})
        if invoice.status not in (
            Invoice.Status.DRAFT,
            Invoice.Status.CONFIRMED,
        ):
            raise ValidationError({"status": "Invoice cannot be cancelled."})
        invoice.status = Invoice.Status.CANCELLED
        invoice.cancelled_at = timezone.now()
        if updated_by is not None:
            invoice.updated_by = updated_by  # type: ignore[assignment]
        invoice.save(
            update_fields=["status", "cancelled_at", "updated_by", "updated_at"]
        )
        return invoice

    @staticmethod
    def delete(*, invoice: Invoice) -> None:
        InvoiceService._ensure_draft(invoice)
        invoice.delete()
