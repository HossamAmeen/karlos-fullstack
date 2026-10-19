"""Soft-delete guarantees: every domain model must be soft-deletable."""

from decimal import Decimal

import pytest
from django.apps import apps
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.expenses.models import Expense, ExpenseCategory, ExpenseMainCategory
from apps.invoices.models import Invoice, InvoicePiece, Payment
from apps.services.models import Service, ServiceCategory
from utils.models import BaseModel

# Models that are intentionally NOT soft-deletable (technical counters only).
HARD_DELETE_ALLOWLIST = {"invoices.InvoiceSequence"}


def project_models():
    return [m for m in apps.get_models() if m._meta.app_label in
            {"clients", "services", "invoices", "expenses", "core"}]


def test_every_domain_model_uses_soft_delete_base():
    offenders = [
        m._meta.label
        for m in project_models()
        if m._meta.label not in HARD_DELETE_ALLOWLIST and not issubclass(m, BaseModel)
    ]
    assert offenders == [], f"Models without soft delete: {offenders}"


@pytest.fixture
def api():
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.create_user(username="sd", password="x12345678")
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def graph(db):
    client = Client.objects.create(name="SD", phone="0100")
    cat = ServiceCategory.objects.create(name="SDcat")
    service = Service.objects.create(
        name="SDsvc", service_category=cat, cost=Decimal("10"),
        cost_method=Service.CostMethod.FIXED, is_fixed_cost=True,
    )
    main = ExpenseMainCategory.objects.create(name="SDmain")
    ecat = ExpenseCategory.objects.create(main_category=main, name="SDec")
    expense = Expense.objects.create(
        amount=Decimal("5"), description="d", expense_date="2026-01-01", category=ecat
    )
    return dict(client=client, cat=cat, service=service, main=main, ecat=ecat, expense=expense)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "key,model",
    [
        ("client", Client), ("cat", ServiceCategory), ("service", Service),
        ("expense", Expense), ("ecat", ExpenseCategory), ("main", ExpenseMainCategory),
    ],
)
def test_instance_delete_is_soft_and_restorable(graph, key, model):
    obj = graph[key]
    obj.delete()
    assert not model.objects.filter(pk=obj.pk).exists()
    assert model.all_objects.filter(pk=obj.pk, deleted_at__isnull=False).exists()
    obj = model.all_objects.get(pk=obj.pk)
    obj.restore()
    assert model.objects.filter(pk=obj.pk).exists()


@pytest.mark.django_db
def test_queryset_delete_is_soft(graph):
    Client.objects.all().delete()
    assert Client.objects.count() == 0
    assert Client.all_objects.count() == 1


@pytest.mark.django_db
def test_invoice_graph_soft_delete(graph):
    inv = Invoice.objects.create(number="SD-1", client=graph["client"])
    piece = InvoicePiece.objects.create(invoice=inv)
    pay = Payment.objects.create(client=graph["client"], invoice=inv, amount=Decimal("1"))
    for obj in (pay, piece, inv):
        model = type(obj)
        obj.delete()
        assert not model.objects.filter(pk=obj.pk).exists()
        assert model.all_objects.filter(pk=obj.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "key,detail",
    [
        ("client", "client-detail"), ("cat", "service-category-detail"),
        ("service", "service-detail"), ("expense", "expense-detail"),
        ("ecat", "expense-category-detail"), ("main", "expense-main-category-detail"),
    ],
)
def test_api_delete_soft_deletes_row(api, graph, key, detail):
    obj = graph[key]
    model = type(obj)
    # Remove dependants first so PROTECT rules do not block the delete.
    if key == "cat":
        graph["service"].delete()
    if key == "ecat":
        graph["expense"].delete()
    if key == "main":
        graph["expense"].delete()
        graph["ecat"].delete()
    url = reverse(detail, args=[obj.pk])
    assert api.delete(url).status_code == status.HTTP_204_NO_CONTENT
    assert api.get(url).status_code == status.HTTP_404_NOT_FOUND
    assert model.all_objects.get(pk=obj.pk).deleted_at is not None


@pytest.mark.django_db
def test_api_delete_draft_invoice_is_soft(api, graph):
    inv = Invoice.objects.create(number="SD-2", client=graph["client"])
    url = reverse("invoice-detail", args=[inv.pk])
    assert api.delete(url).status_code == status.HTTP_204_NO_CONTENT
    assert api.get(url).status_code == status.HTTP_404_NOT_FOUND
    assert Invoice.all_objects.get(pk=inv.pk).deleted_at is not None
    assert api.get(reverse("invoice-list")).data["count"] == 0
