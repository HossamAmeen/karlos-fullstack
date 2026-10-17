import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.services.models import ServiceCategory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestExpenseAPI:
    def test_create_expense(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)

        # Validation: service_category required for "services"
        url = reverse("expense-list")
        response = api_client.post(
            url,
            {
                "amount": "100.00",
                "description": "Internet Bill",
                "expense_date": "2026-08-01",
                "category": "services",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Create ServiceCategory and retry
        cat = ServiceCategory.objects.create(name="Internet")
        response = api_client.post(
            url,
            {
                "amount": "100.00",
                "description": "Internet Bill",
                "expense_date": "2026-08-01",
                "category": "services",
                "service_category": cat.id,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

        # Check Summary
        summary_url = reverse("expense-summary")
        resp = api_client.get(summary_url)
        assert resp.status_code == status.HTTP_200_OK
        assert float(resp.data["total_expenses"]) == 100.0
        assert float(resp.data["total_services"]) == 100.0
        assert float(resp.data["total_factory"]) == 0.0
