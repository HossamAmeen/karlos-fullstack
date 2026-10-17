import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.expenses.models import ExpenseCategory, ExpenseMainCategory


@pytest.fixture
def api_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def main_category():
    return ExpenseMainCategory.objects.create(name="المصنع")


@pytest.fixture
def category(main_category):
    return ExpenseCategory.objects.create(main_category=main_category, name="كهرباء")


@pytest.mark.django_db
class TestExpenseHierarchyAPI:
    def test_main_category_crud_and_unique(self, api_client):
        url = reverse("expense-main-category-list")
        resp = api_client.post(url, {"name": "الرواتب"})
        assert resp.status_code == status.HTTP_201_CREATED
        pk = resp.data["id"]
        assert api_client.post(url, {"name": "الرواتب"}).status_code == 400

        resp = api_client.put(
            reverse("expense-main-category-detail", args=[pk]), {"name": "مرتبات"}
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["name"] == "مرتبات"

        resp = api_client.delete(reverse("expense-main-category-detail", args=[pk]))
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_cannot_delete_main_category_with_categories(self, api_client, category):
        resp = api_client.delete(
            reverse("expense-main-category-detail", args=[category.main_category_id])
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_category_crud(self, api_client, main_category):
        url = reverse("expense-category-list")
        resp = api_client.post(url, {"main_category": main_category.id, "name": "غاز"})
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["main_category_name"] == "المصنع"
        assert (
            api_client.post(
                url, {"main_category": main_category.id, "name": "غاز"}
            ).status_code
            == 400
        )
        resp = api_client.get(url, {"main_category": main_category.id})
        assert resp.data["count"] == 1

    def test_expense_with_client_and_dynamic_summary(self, api_client, category):
        client = Client.objects.create(name="عميل", phone="010")
        other_main = ExpenseMainCategory.objects.create(name="الرواتب")
        workers = ExpenseCategory.objects.create(main_category=other_main, name="عمال")

        url = reverse("expense-list")
        base = {"description": "x", "expense_date": "2026-08-01"}
        resp = api_client.post(
            url,
            {**base, "amount": "100.00", "category": category.id, "client": client.id},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["main_category_name"] == "المصنع"
        assert resp.data["category_name"] == "كهرباء"
        assert resp.data["client_name"] == "عميل"

        resp = api_client.post(url, {**base, "amount": "50", "category": workers.id})
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["client"] is None

        assert (
            api_client.post(
                url, {**base, "amount": "0", "category": workers.id}
            ).status_code
            == 400
        )

        resp = api_client.get(reverse("expense-summary"))
        assert float(resp.data["total_expenses"]) == 150.0
        totals = {r["main_category_name"]: float(r["total"]) for r in resp.data["by_main_category"]}
        assert totals == {"المصنع": 100.0, "الرواتب": 50.0}

        resp = api_client.get(url, {"main_category": other_main.id})
        assert resp.data["count"] == 1

    def test_cannot_delete_category_in_use(self, api_client, category):
        client = Client.objects.create(name="t", phone="011")
        api_client.post(
            reverse("expense-list"),
            {
                "amount": "5",
                "description": "d",
                "expense_date": "2026-08-01",
                "category": category.id,
                "client": client.id,
            },
        )
        assert (
            api_client.delete(
                reverse("expense-category-detail", args=[category.id])
            ).status_code
            == 400
        )
