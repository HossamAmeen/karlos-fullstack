from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.clients.models import Client
from apps.expenses.models import Expense, ExpenseCategory, ExpenseMainCategory
from apps.invoices.models import Invoice


class StatisticsApiTests(APITestCase):
    def setUp(self) -> None:
        user = get_user_model().objects.create_user(username="u", password="p")
        self.client.force_authenticate(user)
        self.customer = Client.objects.create(name="A", phone="1")
        main = ExpenseMainCategory.objects.create(name="M")
        self.category = ExpenseCategory.objects.create(main_category=main, name="C")

    def _invoice(self, number: str, total: str, issue: date, status_: str) -> None:
        Invoice.objects.create(
            number=number,
            client=self.customer,
            issue_date=issue,
            status=status_,
            total=Decimal(total),
        )

    def _expense(self, amount: str, when: date, client=None) -> None:
        Expense.objects.create(
            amount=Decimal(amount),
            description="x",
            expense_date=when,
            category=self.category,
            client=client,
        )

    def test_requires_authentication(self) -> None:
        self.client.force_authenticate(None)
        response = self.client.get(reverse("statistics"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_totals_month_and_year_profit(self) -> None:
        from django.utils import timezone

        today = timezone.localdate()
        self._invoice("I1", "1000", today, Invoice.Status.CONFIRMED)
        self._invoice("I2", "500", today.replace(month=1, day=1), Invoice.Status.CONFIRMED)
        self._invoice("I3", "999", today, Invoice.Status.DRAFT)
        self._expense("200", today)
        self._expense("50", today.replace(month=1, day=1))
        self._expense("70", date(today.year - 1, 6, 1))

        data = self.client.get(reverse("statistics")).data
        self.assertEqual(data["total_invoices"], Decimal("1500.00"))
        self.assertEqual(data["total_expenses"], Decimal("320.00"))
        self.assertEqual(data["current_money"], Decimal("1180.00"))
        self.assertEqual(data["year"]["profit"], Decimal("1250.00"))
        if today.month == 1:
            self.assertEqual(data["month"]["profit"], Decimal("1250.00"))
        else:
            self.assertEqual(data["month"]["profit"], Decimal("800.00"))

    def test_client_statement_includes_total_expenses(self) -> None:
        self._expense("30", date.today(), client=self.customer)
        self._expense("10", date.today())
        data = self.client.get(
            reverse("client-statement", args=[self.customer.pk])
        ).data
        self.assertEqual(data["total_expenses"], "30.00")
