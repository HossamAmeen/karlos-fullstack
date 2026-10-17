from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self) -> tuple[int, dict[str, int]]:
        count = self.update(deleted_at=timezone.now())
        return count, {self.model._meta.label: count}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()

    def alive(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> SoftDeleteQuerySet:
        return self.exclude(deleted_at__isnull=True)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):  # type: ignore[misc]
    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class BaseModel(models.Model):
    """Abstract base model with audit timestamps and user tracking."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated",
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(
        self, using: Any = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])
        return 1, {self._meta.label: 1}

    def hard_delete(
        self, using: Any = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self) -> None:
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])
