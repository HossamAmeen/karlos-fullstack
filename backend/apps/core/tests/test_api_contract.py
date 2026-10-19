"""Cross-cutting API tests: auth, 401 sweep, 404s, validation and the money flow."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.expenses.models import Expense, ExpenseCategory, ExpenseMainCategory
from apps.invoices.models import Invoice
from apps.services.models import Service, ServiceCategory

PROTECTED_LISTS = [
    "client-list", "service-category-list", "service-list", "invoice-list",
    "expense-main-category-list", "expense-category-list", "expense-list",
    "expense-summary", "statistics",
]


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="01010079798", password="admin")


@pytest.fixture
def api(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def world(db):
    client = Client.objects.create(name="Ali", phone="0101")
    cat = ServiceCategory.objects.create(name="Glass")
    svc = Service.objects.create(
        name="Fix", service_category=cat, cost=Decimal("100"),
        cost_method=Service.CostMethod.FIXED, is_fixed_cost=True,
    )
    return client, cat, svc


def make_confirmed(api, world, paid=None):
    client, _, svc = world
    inv = api.post(reverse("invoice-list"), {"client": client.id}, format="json").data
    api.post(reverse("invoice-add-item", args=[inv["id"]]), {"service": svc.id}, format="json")
    body = {"amount_paid": paid} if paid else {}
    resp = api.post(reverse("invoice-confirm", args=[inv["id"]]), body, format="json")
    assert resp.status_code == 200, resp.data
    return resp.data


# ---- auth ----------------------------------------------------------------
@pytest.mark.django_db
def test_token_login_success_and_failure(user):
    c = APIClient()
    ok = c.post("/api/auth/token/", {"username": "01010079798", "password": "admin"}, format="json")
    assert ok.status_code == 200 and {"access", "refresh"} <= set(ok.data)
    bad = c.post("/api/auth/token/", {"username": "01010079798", "password": "nope"}, format="json")
    assert bad.status_code == 401
    refreshed = c.post("/api/auth/token/refresh/", {"refresh": ok.data["refresh"]}, format="json")
    assert refreshed.status_code == 200 and "access" in refreshed.data
    verify = c.post("/api/auth/token/verify/", {"token": ok.data["access"]}, format="json")
    assert verify.status_code == 200


@pytest.mark.django_db
def test_jwt_bearer_grants_access(user):
    c = APIClient()
    tok = c.post("/api/auth/token/", {"username": "01010079798", "password": "admin"}, format="json").data["access"]
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tok}")
    assert c.get(reverse("client-list")).status_code == 200
    c.credentials(HTTP_AUTHORIZATION="Bearer garbage")
    assert c.get(reverse("client-list")).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("name", PROTECTED_LISTS)
def test_endpoints_require_auth(name):
    assert APIClient().get(reverse(name)).status_code == 401


@pytest.mark.django_db
def test_schema_and_health_public():
    assert APIClient().get(reverse("health")).status_code == 200
    assert APIClient().get(reverse("schema")).status_code in (200, 401)


@pytest.mark.django_db
@pytest.mark.parametrize("name", PROTECTED_LISTS[:-2] + ["expense-list"])
def test_list_endpoints_paginate(api, name):
    data = api.get(reverse(name)).data
    assert {"count", "results"} <= set(data)


# ---- clients ---------------------------------------------------------------
@pytest.mark.django_db
def test_client_validation_search_and_404(api):
    url = reverse("client-list")
    assert api.post(url, {}, format="json").status_code == 400
    api.post(url, {"name": "Zed", "phone": "777"}, format="json")
    api.post(url, {"name": "Amr", "phone": "888"}, format="json")
    assert api.get(url, {"search": "Zed"}).data["count"] == 1
    assert api.get(reverse("client-detail", args=[9999])).status_code == 404
    assert api.get(reverse("client-statement", args=[9999])).status_code == 404


@pytest.mark.django_db
def test_deleted_client_phone_can_be_reused(api):
    url = reverse("client-list")
    cid = api.post(url, {"name": "A", "phone": "555"}, format="json").data["id"]
    api.delete(reverse("client-detail", args=[cid]))
    assert api.post(url, {"name": "B", "phone": "555"}, format="json").status_code == 201


@pytest.mark.django_db
def test_deposit_validation(api, world):
    url = reverse("client-deposits", args=[world[0].id])
    assert api.post(url, {"amount": "0"}, format="json").status_code == 400
    assert api.post(url, {"amount": "-5"}, format="json").status_code == 400
    assert api.post(url, {}, format="json").status_code == 400


@pytest.mark.django_db
def test_cancelled_invoice_payment_counts_as_deposit(api, world):
    inv = make_confirmed(api, world, paid="40.00")
    assert api.post(reverse("invoice-cancel", args=[inv["id"]])).status_code == 200
    st = api.get(reverse("client-statement", args=[world[0].id])).data
    assert st["total_charged"] == "0.00"
    assert st["total_deposits"] == "40.00"
    assert st["balance_due"] == "-40.00"


# ---- invoices ----------------------------------------------------------------
@pytest.mark.django_db
def test_invoice_requires_client_and_valid_actions(api, world):
    assert api.post(reverse("invoice-list"), {}, format="json").status_code == 400
    assert api.post(reverse("invoice-confirm", args=[9999]), {}, format="json").status_code == 404


@pytest.mark.django_db
def test_cannot_pay_draft_or_cancel_twice(api, world):
    client, _, svc = world
    inv = api.post(reverse("invoice-list"), {"client": client.id}, format="json").data
    assert api.post(reverse("invoice-pay", args=[inv["id"]]), {"amount": "5"}, format="json").status_code == 400
    api.post(reverse("invoice-add-item", args=[inv["id"]]), {"service": svc.id}, format="json")
    api.post(reverse("invoice-confirm", args=[inv["id"]]), {}, format="json")
    assert api.post(reverse("invoice-cancel", args=[inv["id"]])).status_code == 200
    assert api.post(reverse("invoice-cancel", args=[inv["id"]])).status_code == 400


@pytest.mark.django_db
def test_confirmed_invoice_cannot_be_deleted(api, world):
    inv = make_confirmed(api, world)
    resp = api.delete(reverse("invoice-detail", args=[inv["id"]]))
    assert resp.status_code == 400
    assert Invoice.objects.filter(pk=inv["id"]).exists()


@pytest.mark.django_db
def test_amount_paid_cannot_exceed_total(api, world):
    client, _, svc = world
    inv = api.post(reverse("invoice-list"), {"client": client.id}, format="json").data
    api.post(reverse("invoice-add-item", args=[inv["id"]]), {"service": svc.id}, format="json")
    resp = api.post(reverse("invoice-confirm", args=[inv["id"]]), {"amount_paid": "101"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_invoice_totals_unaffected_by_client_supplied_total(api, world):
    client, _, svc = world
    inv = api.post(reverse("invoice-list"), {"client": client.id, "total": "1"}, format="json").data
    api.post(reverse("invoice-add-item", args=[inv["id"]]), {"service": svc.id}, format="json")
    got = api.get(reverse("invoice-detail", args=[inv["id"]])).data
    assert got["total"] == "100.00"


# ---- services ------------------------------------------------------------------
@pytest.mark.django_db
def test_service_color_default_and_search(api, world):
    _, cat, _ = world
    resp = api.post(reverse("service-list"), {
        "name": "Tint", "service_category": cat.id, "cost": "3", "cost_method": "fixed",
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["color"] == "#3b82f6"
    assert api.get(reverse("service-list"), {"search": "Tint"}).data["count"] == 1


@pytest.mark.django_db
def test_category_soft_delete_does_not_cascade_to_services(api, world):
    resp = api.delete(reverse("service-category-detail", args=[world[1].id]))
    assert resp.status_code == 204
    assert ServiceCategory.all_objects.get(pk=world[1].id).deleted_at is not None
    assert Service.objects.filter(pk=world[2].id).exists()


# ---- expenses --------------------------------------------------------------------
@pytest.mark.django_db
def test_expense_update_delete_and_filters(api):
    main = ExpenseMainCategory.objects.create(name="M")
    cat = ExpenseCategory.objects.create(main_category=main, name="C")
    url = reverse("expense-list")
    created = api.post(url, {
        "amount": "10", "description": "d", "expense_date": "2026-03-01", "category": cat.id,
    }, format="json")
    assert created.status_code == 201
    eid = created.data["id"]
    patched = api.patch(reverse("expense-detail", args=[eid]), {"amount": "12.50"}, format="json")
    assert patched.status_code == 200 and patched.data["amount"] == "12.50"
    assert api.get(url, {"start_date": "2026-04-01"}).data["count"] == 0
    assert api.get(url, {"start_date": "2026-03-01", "end_date": "2026-03-31"}).data["count"] == 1
    assert api.delete(reverse("expense-detail", args=[eid])).status_code == 204
    assert Expense.all_objects.get(pk=eid).deleted_at is not None
    summary = api.get(reverse("expense-summary")).data
    assert float(summary["total_expenses"]) == 0.0


# ---- statistics ---------------------------------------------------------------------
@pytest.mark.django_db
def test_statistics_shape(api):
    data = api.get(reverse("statistics")).data
    assert {"total_invoices", "total_expenses", "current_money", "month", "year"} <= set(data)
    assert "profit" in data["month"] and "profit" in data["year"]
