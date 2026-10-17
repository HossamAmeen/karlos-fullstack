from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import (
    ExpenseCategoryFilter,
    ExpenseFilter,
    ExpenseMainCategoryFilter,
)
from .selectors import (
    get_categories,
    get_expenses,
    get_expenses_summary,
    get_main_categories,
)
from .serializers import (
    ExpenseCategorySerializer,
    ExpenseMainCategorySerializer,
    ExpenseSerializer,
)
from .services import (
    ExpenseCategoryService,
    ExpenseMainCategoryService,
)


class ExpenseMainCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseMainCategorySerializer
    filterset_class = ExpenseMainCategoryFilter
    search_fields = ["name"]
    ordering_fields = ["id", "name", "created_at", "updated_at"]
    ordering = ["name", "id"]

    def get_queryset(self):
        return get_main_categories()

    def destroy(self, request, *args, **kwargs):
        ExpenseMainCategoryService.delete(category=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseCategorySerializer
    filterset_class = ExpenseCategoryFilter
    search_fields = ["name", "main_category__name"]
    ordering_fields = ["id", "name", "created_at", "updated_at"]
    ordering = ["main_category__name", "name", "id"]

    def get_queryset(self):
        return get_categories()

    def destroy(self, request, *args, **kwargs):
        ExpenseCategoryService.delete(category=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    filterset_class = ExpenseFilter
    search_fields = ["description"]
    ordering_fields = ["expense_date", "id", "amount", "created_at", "updated_at"]

    def get_queryset(self):
        return get_expenses(filters=self.request.query_params)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "date", type=str, description="Single Date (YYYY-MM-DD)", required=False
            ),
            OpenApiParameter(
                "start_date",
                type=str,
                description="Start Date (YYYY-MM-DD)",
                required=False,
            ),
            OpenApiParameter(
                "end_date",
                type=str,
                description="End Date (YYYY-MM-DD)",
                required=False,
            ),
            OpenApiParameter(
                "main_category",
                type=int,
                description="Expense Main Category ID",
                required=False,
            ),
            OpenApiParameter(
                "category", type=int, description="Expense Category ID", required=False
            ),
            OpenApiParameter(
                "client", type=int, description="Client ID", required=False
            ),
        ]
    )
    @action(detail=False, methods=["get"])
    def summary(self, request):
        summary_data = get_expenses_summary(filters=request.query_params)
        return Response(summary_data)
