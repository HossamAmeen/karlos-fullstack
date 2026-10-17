from django.db.models import QuerySet

from apps.services.models import Service, ServiceCategory


class ServiceCategorySelector:
    @staticmethod
    def all() -> QuerySet[ServiceCategory]:
        return ServiceCategory.objects.all()

    @staticmethod
    def by_id(*, category_id: int) -> ServiceCategory:
        return ServiceCategory.objects.get(pk=category_id)


class ServiceSelector:
    @staticmethod
    def all() -> QuerySet[Service]:
        return Service.objects.select_related("service_category").all()

    @staticmethod
    def by_id(*, service_id: int) -> Service:
        return Service.objects.select_related("service_category").get(pk=service_id)
