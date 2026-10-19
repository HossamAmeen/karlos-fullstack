from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .backup import BackupError, run_backup
from .selectors import get_statistics


class HealthView(APIView):
    """Liveness/readiness probe: public, reports DB connectivity."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(tags=["health"], responses={200: dict, 503: dict})
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            return Response(
                {"status": "error", "database": "unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {"status": "ok", "database": "ok", "version": settings.APP_VERSION}
        )


class StatisticsView(APIView):
    """Totals of bills / expenses plus current month and year profit."""

    @extend_schema(tags=["statistics"], responses={200: dict})
    def get(self, request):
        return Response(get_statistics())


class BackupView(APIView):
    """Create a database backup file on the server (staff only)."""

    permission_classes = [IsAdminUser]

    @extend_schema(tags=["backup"], request=None, responses={201: dict, 500: dict})
    def post(self, request):
        try:
            result = run_backup()
        except BackupError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        if result["mode"] == "celery":
            return Response(result, status=status.HTTP_202_ACCEPTED)
        return Response(result, status=status.HTTP_201_CREATED)
