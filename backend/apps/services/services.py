from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser

from apps.services.models import Service, ServiceCategory


UNSET = object()


class ServiceCategoryService:
    @staticmethod
    def create(
        *,
        name: str,
        icon=None,
        created_by: AbstractBaseUser | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> ServiceCategory:
        return ServiceCategory.objects.create(
            name=name.strip(),
            icon=icon,
            created_by=created_by,
            updated_by=updated_by if updated_by is not None else created_by,
        )

    @staticmethod
    def update(
        *,
        category: ServiceCategory,
        name: str,
        icon=UNSET,
        updated_by: AbstractBaseUser | None = None,
    ) -> ServiceCategory:
        category.name = name.strip()
        fields = ["name", "updated_by", "updated_at"]
        if icon is not UNSET:
            category.icon = icon
            fields.append("icon")
        if updated_by is not None:
            category.updated_by = updated_by  # type: ignore[assignment]
        category.save(update_fields=fields)
        return category

    @staticmethod
    def delete(*, category: ServiceCategory) -> None:
        category.delete()


class ServiceService:
    @staticmethod
    def create(
        *,
        name: str,
        service_category: ServiceCategory,
        cost: Decimal,
        cost_method: str = Service.CostMethod.TWO_DIMENSIONS,
        is_fixed_cost: bool = False,
        is_additional_service: bool = False,
        color: str = "#3b82f6",
        icon=None,
        created_by: AbstractBaseUser | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Service:
        return Service.objects.create(
            name=name.strip(),
            service_category=service_category,
            cost=cost,
            cost_method=cost_method,
            is_fixed_cost=is_fixed_cost,
            is_additional_service=is_additional_service,
            color=color,
            icon=icon,
            created_by=created_by,
            updated_by=updated_by if updated_by is not None else created_by,
        )

    @staticmethod
    def update(
        *,
        service: Service,
        name: str,
        service_category: ServiceCategory,
        cost: Decimal,
        cost_method: str,
        is_fixed_cost: bool,
        is_additional_service: bool,
        color: str,
        icon=UNSET,
        updated_by: AbstractBaseUser | None = None,
    ) -> Service:
        service.name = name.strip()
        service.service_category = service_category
        service.cost = cost
        service.cost_method = cost_method
        service.is_fixed_cost = is_fixed_cost
        service.is_additional_service = is_additional_service
        service.color = color
        fields = [
            "name",
            "service_category",
            "cost",
            "cost_method",
            "is_fixed_cost",
            "is_additional_service",
            "color",
            "updated_by",
            "updated_at",
        ]
        if icon is not UNSET:
            service.icon = icon
            fields.append("icon")
        if updated_by is not None:
            service.updated_by = updated_by  # type: ignore[assignment]
        service.save(update_fields=fields)
        return service

    @staticmethod
    def delete(*, service: Service) -> None:
        service.delete()
