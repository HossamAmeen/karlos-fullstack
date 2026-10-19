from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.invoices.filters import InvoiceFilter
from apps.invoices.models import Invoice, InvoiceItem, InvoicePiece
from apps.invoices.selectors import InvoiceSelector
from apps.invoices.serializers import (
    InvoiceConfirmSerializer,
    InvoiceItemWriteSerializer,
    InvoicePaymentSerializer,
    InvoicePieceUpdateSerializer,
    InvoicePieceWriteSerializer,
    InvoiceSerializer,
    _django_to_drf,
)
from apps.invoices.services import InvoiceService


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    filterset_class = InvoiceFilter
    search_fields = ("number", "client__name", "client__phone", "notes")
    ordering_fields = ("id", "number", "issue_date", "status", "total", "created_at")
    ordering = ("-issue_date", "-id")
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if self.action in (
            "retrieve",
            "partial_update",
            "add_item",
            "item_detail",
            "add_piece",
            "piece_detail",
            "confirm",
            "cancel",
            "pay",
        ):
            return InvoiceSelector.detail_queryset()
        return InvoiceSelector.all()

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance: Invoice = self.get_object()
        try:
            InvoiceService.delete(invoice=instance)
        except DjangoValidationError as exc:
            _django_to_drf(exc)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="items")
    def add_item(self, request: Request, pk=None) -> Response:
        invoice = self.get_object()
        serializer = InvoiceItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user if request.user.is_authenticated else None
        try:
            invoice = InvoiceService.add_item(
                invoice=invoice,
                service=data["service"],
                unit_price=data.get("unit_price"),
                quantity=data.get("quantity"),
                length=data.get("length"),
                width=data.get("width"),
                measure=data.get("measure"),
                discount_amount=data.get("discount_amount", Decimal("0")),
                piece=data.get("piece"),
                piece_quantity=data.get("piece_quantity"),
                created_by=user,
                updated_by=user,
            )
        except DjangoValidationError as exc:
            _django_to_drf(exc)
        invoice = InvoiceSelector.by_id(invoice_id=invoice.pk)
        return Response(
            InvoiceSerializer(invoice, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"items/(?P<item_id>[^/.]+)",
    )
    def item_detail(self, request: Request, pk=None, item_id=None) -> Response:
        invoice = self.get_object()
        try:
            item = InvoiceItem.objects.get(pk=item_id, invoice=invoice)
        except InvoiceItem.DoesNotExist:
            return Response(
                {"detail": "Item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user if request.user.is_authenticated else None
        try:
            if request.method == "DELETE":
                invoice = InvoiceService.remove_item(invoice=invoice, item=item)
            else:
                serializer = InvoiceItemWriteSerializer(data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                data = serializer.validated_data
                invoice = InvoiceService.update_item(
                    invoice=invoice,
                    item=item,
                    unit_price=data.get("unit_price"),
                    quantity=data.get("quantity"),
                    length=data.get("length"),
                    width=data.get("width"),
                    measure=data.get("measure"),
                    discount_amount=data.get("discount_amount"),
                    updated_by=user,
                )
        except DjangoValidationError as exc:
            _django_to_drf(exc)

        invoice = InvoiceSelector.by_id(invoice_id=invoice.pk)
        return Response(InvoiceSerializer(invoice, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="pieces")
    def add_piece(self, request: Request, pk=None) -> Response:
        invoice = self.get_object()
        serializer = InvoicePieceWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user if request.user.is_authenticated else None
        try:
            invoice = InvoiceService.add_piece(
                invoice=invoice,
                length=data.get("length"),
                width=data.get("width"),
                quantity=data.get("quantity", Decimal("1")),
                notes=data.get("notes", ""),
                items=data["items"],
                created_by=user,
                updated_by=user,
            )
        except DjangoValidationError as exc:
            _django_to_drf(exc)
        invoice = InvoiceSelector.by_id(invoice_id=invoice.pk)
        return Response(
            InvoiceSerializer(invoice, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"pieces/(?P<piece_id>[^/.]+)",
    )
    def piece_detail(self, request: Request, pk=None, piece_id=None) -> Response:
        invoice = self.get_object()
        try:
            piece = InvoicePiece.objects.get(pk=piece_id, invoice=invoice)
        except InvoicePiece.DoesNotExist:
            return Response(
                {"detail": "Piece not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user if request.user.is_authenticated else None
        try:
            if request.method == "DELETE":
                invoice = InvoiceService.remove_piece(invoice=invoice, piece=piece)
            else:
                serializer = InvoicePieceUpdateSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                data = serializer.validated_data
                invoice = InvoiceService.update_piece(
                    invoice=invoice,
                    piece=piece,
                    length=data.get("length"),
                    width=data.get("width"),
                    quantity=data.get("quantity"),
                    notes=data.get("notes"),
                    updated_by=user,
                )
        except DjangoValidationError as exc:
            _django_to_drf(exc)

        invoice = InvoiceSelector.by_id(invoice_id=invoice.pk)
        return Response(InvoiceSerializer(invoice, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request: Request, pk=None) -> Response:
        invoice = self.get_object()
        serializer = InvoiceConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        try:
            invoice = InvoiceService.confirm(
                invoice=invoice,
                amount_paid=serializer.validated_data.get("amount_paid"),
                updated_by=user,
            )
        except DjangoValidationError as exc:
            _django_to_drf(exc)
        invoice = InvoiceSelector.by_id(invoice_id=invoice.pk)
        return Response(InvoiceSerializer(invoice, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="pay")
    def pay(self, request: Request, pk=None) -> Response:
        invoice = self.get_object()
        serializer = InvoicePaymentSerializer(
            data=request.data,
            context={"invoice": invoice},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user if request.user.is_authenticated else None
        try:
            InvoiceService.record_payment(
                invoice=invoice,
                amount=data["amount"],
                paid_at=data.get("paid_at"),
                notes=data.get("notes", ""),
                created_by=user,
                updated_by=user,
            )
        except DjangoValidationError as exc:
            _django_to_drf(exc)
        invoice = InvoiceSelector.by_id(invoice_id=invoice.pk)
        return Response(InvoiceSerializer(invoice, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request: Request, pk=None) -> Response:
        invoice = self.get_object()
        user = request.user if request.user.is_authenticated else None
        try:
            invoice = InvoiceService.cancel(invoice=invoice, updated_by=user)
        except DjangoValidationError as exc:
            _django_to_drf(exc)
        invoice = InvoiceSelector.by_id(invoice_id=invoice.pk)
        return Response(InvoiceSerializer(invoice, context={"request": request}).data)
