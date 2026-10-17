from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import ExpenseFilter
from .selectors import get_expenses, get_expenses_summary
from .serializers import ExpenseSerializer


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
                "category", type=str, description="Main Category", required=False
            ),
            OpenApiParameter(
                "service_category",
                type=int,
                description="Service Category ID",
                required=False,
            ),
        ]
    )
    @action(detail=False, methods=["get"])
    def summary(self, request):
        summary_data = get_expenses_summary(filters=request.query_params)
        return Response(summary_data)
