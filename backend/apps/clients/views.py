from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.clients.filters import ClientFilter
from apps.clients.models import Client
from apps.clients.selectors import ClientSelector
from apps.clients.serializers import (
    ClientDepositWriteSerializer,
    ClientSerializer,
    ClientStatementSerializer,
    _django_to_drf,
)
from apps.clients.services import ClientService


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    filterset_class = ClientFilter
    search_fields = ("name", "phone", "email")
    ordering_fields = ("id", "name", "created_at", "updated_at")
    ordering = ("name", "id")

    def get_queryset(self):
        return ClientSelector.all()

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance: Client = self.get_object()
        ClientService.delete(client=instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="statement")
    def statement(self, request: Request, pk=None) -> Response:
        client = self.get_object()
        data = ClientSelector.statement(client=client)
        return Response(
            ClientStatementSerializer(data, context={"request": request}).data
        )

    @action(detail=True, methods=["post"], url_path="deposits")
    def deposits(self, request: Request, pk=None) -> Response:
        client = self.get_object()
        serializer = ClientDepositWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user if request.user.is_authenticated else None
        try:
            ClientService.record_deposit(
                client=client,
                amount=data["amount"],
                paid_at=data.get("paid_at"),
                notes=data.get("notes", ""),
                created_by=user,
                updated_by=user,
            )
        except DjangoValidationError as exc:
            _django_to_drf(exc)
        statement = ClientSelector.statement(client=client)
        return Response(
            ClientStatementSerializer(statement, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
