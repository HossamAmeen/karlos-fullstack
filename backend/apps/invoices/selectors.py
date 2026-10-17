from django.db.models import Prefetch, QuerySet

from apps.invoices.models import Invoice, InvoiceItem, InvoicePiece


class InvoiceSelector:
    @staticmethod
    def all() -> QuerySet[Invoice]:
        return Invoice.objects.select_related("client").all()

    @staticmethod
    def detail_queryset() -> QuerySet[Invoice]:
        item_qs = InvoiceItem.objects.select_related("service").all()
        piece_qs = InvoicePiece.objects.prefetch_related(
            Prefetch(
                "items",
                queryset=InvoiceItem.objects.select_related("service").all(),
            )
        )
        return Invoice.objects.select_related("client").prefetch_related(
            Prefetch("pieces", queryset=piece_qs),
            Prefetch("items", queryset=item_qs),
        )

    @staticmethod
    def by_id(*, invoice_id: int) -> Invoice:
        return InvoiceSelector.detail_queryset().get(pk=invoice_id)
