import django_filters

from apps.services.models import Service, ServiceCategory


class ServiceCategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = ServiceCategory
        fields = ("name",)


class ServiceFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    service_category = django_filters.NumberFilter(field_name="service_category_id")
    cost_method = django_filters.ChoiceFilter(choices=Service.CostMethod.choices)
    is_fixed_cost = django_filters.BooleanFilter()
    is_additional_service = django_filters.BooleanFilter()

    class Meta:
        model = Service
        fields = (
            "name",
            "service_category",
            "cost_method",
            "is_fixed_cost",
            "is_additional_service",
        )
