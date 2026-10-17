import django_filters

from apps.expenses.models import (
    Expense,
    ExpenseCategory,
    ExpenseMainCategory,
)


class ExpenseMainCategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = ExpenseMainCategory
        fields = ["name"]


class ExpenseCategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    main_category = django_filters.NumberFilter(field_name="main_category_id")

    class Meta:
        model = ExpenseCategory
        fields = ["name", "main_category"]


class ExpenseFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="expense_date", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="expense_date", lookup_expr="lte")
    date = django_filters.DateFilter(field_name="expense_date")
    category = django_filters.NumberFilter(field_name="category_id")
    main_category = django_filters.NumberFilter(field_name="category__main_category_id")
    client = django_filters.NumberFilter(field_name="client_id")

    class Meta:
        model = Expense
        fields = ["category", "main_category", "client", "date", "start_date", "end_date"]
