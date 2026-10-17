import django_filters

from apps.clients.models import Client


class ClientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    phone = django_filters.CharFilter(lookup_expr="icontains")
    email = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Client
        fields = ("name", "phone", "email")
