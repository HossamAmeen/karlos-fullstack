from __future__ import annotations

from typing import Any, cast

from django.contrib.auth.models import AbstractBaseUser
from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """ModelSerializer that stamps created_by / updated_by from request.user."""

    def get_current_user(self) -> AbstractBaseUser | None:
        request = self.context.get("request")
        if request is None:
            return None
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return None
        return cast(AbstractBaseUser, user)

    def assign_audit_on_create(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        user = self.get_current_user()
        if user is not None:
            validated_data["created_by"] = user
            validated_data["updated_by"] = user
        return validated_data

    def assign_audit_on_update(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        user = self.get_current_user()
        if user is not None:
            validated_data["updated_by"] = user
        return validated_data

    def create(self, validated_data: dict[str, Any]):
        validated_data = self.assign_audit_on_create(validated_data)
        return super().create(validated_data)

    def update(self, instance: Any, validated_data: dict[str, Any]):
        validated_data = self.assign_audit_on_update(validated_data)
        return super().update(instance, validated_data)
