import django_filters

from apps.invoices.models import Invoice, Payment


class InvoiceFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(lookup_expr="exact")
    client = django_filters.NumberFilter(field_name="client_id")
    issue_date = django_filters.DateFilter()
    issue_date_from = django_filters.DateFilter(
        field_name="issue_date", lookup_expr="gte"
    )
    issue_date_to = django_filters.DateFilter(
        field_name="issue_date", lookup_expr="lte"
    )

    class Meta:
        model = Invoice
        fields = ("status", "client", "issue_date")


class PaymentFilter(django_filters.FilterSet):
    client = django_filters.NumberFilter(field_name="client_id")
    invoice = django_filters.NumberFilter(field_name="invoice_id")
    method = django_filters.CharFilter(lookup_expr="exact")
    date = django_filters.DateFilter(field_name="paid_at")
    start_date = django_filters.DateFilter(field_name="paid_at", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="paid_at", lookup_expr="lte")

    class Meta:
        model = Payment
        fields = ("client", "invoice", "method", "date", "start_date", "end_date")
