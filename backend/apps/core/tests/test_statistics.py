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


class StatisticsPeriodTests(StatisticsApiTests):
    def test_period_filter_and_payments(self) -> None:
        from apps.invoices.models import Payment

        self._invoice("P1", "100", date(2025, 3, 5), Invoice.Status.CONFIRMED)
        self._invoice("P2", "40", date(2025, 4, 5), Invoice.Status.CONFIRMED)
        self._expense("10", date(2025, 3, 6))
        Payment.objects.create(
            client=self.customer, amount=Decimal("25"), paid_at=date(2025, 3, 7)
        )
        data = self.client.get(
            reverse("statistics"),
            {"date_from": "2025-03-01", "date_to": "2025-03-31"},
        ).data["period"]
        self.assertEqual(data["invoices"], Decimal("100.00"))
        self.assertEqual(data["payments"], Decimal("25.00"))
        self.assertEqual(data["expenses"], Decimal("10.00"))
        self.assertEqual(data["profit"], Decimal("90.00"))
        self.assertEqual(data["group"], "day")
        self.assertEqual(len(data["series"]), 31)

    def test_year_range_groups_by_month(self) -> None:
        data = self.client.get(
            reverse("statistics"),
            {"date_from": "2025-01-01", "date_to": "2025-12-31"},
        ).data["period"]
        self.assertEqual(data["group"], "month")
        self.assertEqual(len(data["series"]), 12)

    def test_invalid_date(self) -> None:
        r = self.client.get(reverse("statistics"), {"date_from": "nope"})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_today_boxes(self) -> None:
        from django.utils import timezone

        from apps.invoices.models import Payment

        today = timezone.localdate()
        Payment.objects.create(client=self.customer, amount=Decimal("90"), paid_at=today)
        Payment.objects.create(
            client=self.customer, amount=Decimal("5"), paid_at=date(2020, 1, 1)
        )
        self._expense("30", today)
        data = self.client.get(reverse("statistics")).data["today"]
        self.assertEqual(data["payments"], Decimal("90.00"))
        self.assertEqual(data["expenses"], Decimal("30.00"))
        self.assertEqual(data["cash"], Decimal("60.00"))
