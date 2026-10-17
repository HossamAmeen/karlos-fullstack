import django_filters

from apps.expenses.models import Expense


class ExpenseFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="expense_date", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="expense_date", lookup_expr="lte")
    date = django_filters.DateFilter(field_name="expense_date")

    class Meta:
        model = Expense
        fields = ["category", "service_category", "date", "start_date", "end_date"]
