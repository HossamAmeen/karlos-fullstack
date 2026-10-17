from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from apps.services.filters import ServiceCategoryFilter, ServiceFilter
from apps.services.models import Service, ServiceCategory
from apps.services.selectors import ServiceCategorySelector, ServiceSelector
from apps.services.serializers import ServiceCategorySerializer, ServiceSerializer
from apps.services.services import ServiceCategoryService, ServiceService


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceCategorySerializer
    filterset_class = ServiceCategoryFilter
    search_fields = ("name",)
    ordering_fields = ("id", "name", "created_at", "updated_at")
    ordering = ("name", "id")

    def get_queryset(self):
        return ServiceCategorySelector.all()

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance: ServiceCategory = self.get_object()
        ServiceCategoryService.delete(category=instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    filterset_class = ServiceFilter
    search_fields = ("name", "service_category__name")
    ordering_fields = ("id", "name", "cost", "cost_method", "created_at", "updated_at")
    ordering = ("name", "id")

    def get_queryset(self):
        return ServiceSelector.all()

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance: Service = self.get_object()
        ServiceService.delete(service=instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
