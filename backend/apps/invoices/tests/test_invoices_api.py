from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.clients.models import Client
from apps.invoices.models import Invoice, InvoiceItem
from apps.services.models import Service, ServiceCategory

User = get_user_model()


class InvoiceApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="invuser", password="pass12345")
        self.list_url = reverse("invoice-list")
        self.client_obj = Client.objects.create(name="Ali", phone="01000000001")
        self.category = ServiceCategory.objects.create(name="Glass")
        self.fixed_service = Service.objects.create(
            name="Fixed install",
            service_category=self.category,
            cost=Decimal("100.00"),
            cost_method=Service.CostMethod.FIXED,
            is_fixed_cost=True,
        )
        self.one_dim_service = Service.objects.create(
            name="One dim glass",
            service_category=self.category,
            cost=Decimal("10.00"),
            cost_method=Service.CostMethod.ONE_DIMENSION,
        )
        self.qty_service = Service.objects.create(
            name="Qty panes",
            service_category=self.category,
            cost=Decimal("25.00"),
            cost_method=Service.CostMethod.QUANTITY,
        )
        self.two_dim_service = Service.objects.create(
            name="Two dim frame",
            service_category=self.category,
            cost=Decimal("5.00"),
            cost_method=Service.CostMethod.TWO_DIMENSIONS,
        )

    def authenticate(self) -> None:
        self.client.force_authenticate(user=self.user)

    def create_draft(self, **overrides) -> dict:
        payload = {
            "client": self.client_obj.id,
            "discount_amount": "0.00",
            "notes": "test",
        }
        payload.update(overrides)
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return dict(response.data)

    def test_requires_authentication(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_draft_generates_number_and_updates_flow(self) -> None:
        self.authenticate()
        data = self.create_draft()
        self.assertTrue(data["number"].startswith("INV-"))
        self.assertEqual(data["status"], Invoice.Status.DRAFT)
        self.assertEqual(data["total"], "0.00")
        self.assertEqual(data["items"], [])

        detail_url = reverse("invoice-detail", args=[data["id"]])
        patch = self.client.patch(
            detail_url,
            {"discount_amount": "0.00", "notes": "updated"},
            format="json",
        )
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertEqual(patch.data["notes"], "updated")

    def test_add_items_all_cost_methods_and_totals(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        items_url = reverse("invoice-add-item", args=[invoice["id"]])

        fixed = self.client.post(
            items_url,
            {"service": self.fixed_service.id, "discount_amount": "10.00"},
            format="json",
        )
        self.assertEqual(fixed.status_code, status.HTTP_201_CREATED, fixed.data)
        self.assertEqual(fixed.data["items"][0]["line_subtotal"], "100.00")
        self.assertEqual(fixed.data["items"][0]["line_total"], "90.00")
        self.assertEqual(fixed.data["subtotal"], "90.00")

        one_dim = self.client.post(
            items_url,
            {
                "service": self.one_dim_service.id,
                "width": "100.00",
                "unit_price": "900.00",
            },
            format="json",
        )
        self.assertEqual(one_dim.status_code, status.HTTP_201_CREATED, one_dim.data)
        # 900 * (100cm x 100cm = 1 m2) = 900
        self.assertEqual(one_dim.data["items"][1]["line_total"], "900.00")
        self.assertEqual(one_dim.data["subtotal"], "990.00")

        qty = self.client.post(
            items_url,
            {"service": self.qty_service.id, "quantity": "4"},
            format="json",
        )
        self.assertEqual(qty.status_code, status.HTTP_201_CREATED, qty.data)
        self.assertEqual(qty.data["items"][2]["line_total"], "100.00")
        self.assertEqual(qty.data["subtotal"], "1090.00")

        two_dim = self.client.post(
            items_url,
            {
                "service": self.two_dim_service.id,
                "length": "100.00",
                "width": "100.00",
            },
            format="json",
        )
        self.assertEqual(two_dim.status_code, status.HTTP_201_CREATED, two_dim.data)
        # 5 * 2*(1+1) = 20
        self.assertEqual(two_dim.data["items"][3]["line_total"], "20.00")
        self.assertEqual(two_dim.data["subtotal"], "1110.00")
        self.assertEqual(two_dim.data["total"], "1110.00")

    def test_item_discount_cannot_exceed_line(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        items_url = reverse("invoice-add-item", args=[invoice["id"]])
        response = self.client.post(
            items_url,
            {
                "service": self.fixed_service.id,
                "discount_amount": "150.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_discount_cannot_exceed_subtotal(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        items_url = reverse("invoice-add-item", args=[invoice["id"]])
        self.client.post(
            items_url,
            {"service": self.fixed_service.id},
            format="json",
        )
        detail_url = reverse("invoice-detail", args=[invoice["id"]])
        response = self.client.patch(
            detail_url,
            {"discount_amount": "200.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_requires_items_and_locks_edits(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        confirm_url = reverse("invoice-confirm", args=[invoice["id"]])
        empty = self.client.post(confirm_url, {}, format="json")
        self.assertEqual(empty.status_code, status.HTTP_400_BAD_REQUEST)

        items_url = reverse("invoice-add-item", args=[invoice["id"]])
        self.client.post(
            items_url,
            {"service": self.fixed_service.id},
            format="json",
        )
        confirmed = self.client.post(confirm_url, {}, format="json")
        self.assertEqual(confirmed.status_code, status.HTTP_200_OK)
        self.assertEqual(confirmed.data["status"], Invoice.Status.CONFIRMED)

        blocked = self.client.post(
            items_url,
            {"service": self.fixed_service.id},
            format="json",
        )
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_and_delete_item(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        items_url = reverse("invoice-add-item", args=[invoice["id"]])
        created = self.client.post(
            items_url,
            {"service": self.qty_service.id, "quantity": "2"},
            format="json",
        )
        item_id = created.data["items"][0]["id"]
        item_url = reverse(
            "invoice-item-detail",
            args=[invoice["id"], item_id],
        )

        updated = self.client.patch(
            item_url,
            {"quantity": "5"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK, updated.data)
        self.assertEqual(updated.data["items"][0]["line_total"], "125.00")
        self.assertEqual(updated.data["total"], "125.00")

        deleted = self.client.delete(item_url)
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        self.assertEqual(deleted.data["items"], [])
        self.assertEqual(deleted.data["total"], "0.00")
        self.assertFalse(InvoiceItem.objects.filter(pk=item_id).exists())

    def test_cancel_invoice(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        cancel_url = reverse("invoice-cancel", args=[invoice["id"]])
        response = self.client.post(cancel_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Invoice.Status.CANCELLED)

    def test_sequential_numbers(self) -> None:
        self.authenticate()
        first = self.create_draft()
        second = self.create_draft()
        self.assertNotEqual(first["number"], second["number"])
        self.assertTrue(second["number"] > first["number"])

    def test_list_filter_by_status(self) -> None:
        self.authenticate()
        draft = self.create_draft()
        items_url = reverse("invoice-add-item", args=[draft["id"]])
        self.client.post(
            items_url,
            {"service": self.fixed_service.id},
            format="json",
        )
        self.client.post(
            reverse("invoice-confirm", args=[draft["id"]]), {}, format="json"
        )
        self.create_draft()

        listed = self.client.get(self.list_url, {"status": Invoice.Status.CONFIRMED})
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(listed.data["count"], 1)
        self.assertEqual(listed.data["results"][0]["status"], Invoice.Status.CONFIRMED)

    def test_confirm_with_full_and_partial_payment(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        items_url = reverse("invoice-add-item", args=[invoice["id"]])
        self.client.post(
            items_url,
            {"service": self.fixed_service.id},
            format="json",
        )
        confirm_url = reverse("invoice-confirm", args=[invoice["id"]])
        partial = self.client.post(confirm_url, {"amount_paid": "40.00"}, format="json")
        self.assertEqual(partial.status_code, status.HTTP_200_OK, partial.data)
        self.assertEqual(partial.data["amount_paid"], "40.00")
        self.assertEqual(partial.data["amount_remaining"], "60.00")
        self.assertEqual(partial.data["payment_status"], "partial")
        self.assertFalse(partial.data["is_settled"])

        pay_url = reverse("invoice-pay", args=[invoice["id"]])
        paid = self.client.post(pay_url, {"amount": "60.00"}, format="json")
        self.assertEqual(paid.status_code, status.HTTP_200_OK, paid.data)
        self.assertEqual(paid.data["amount_paid"], "100.00")
        self.assertEqual(paid.data["amount_remaining"], "0.00")
        self.assertEqual(paid.data["payment_status"], "paid")
        self.assertTrue(paid.data["is_settled"])

        overpay = self.client.post(pay_url, {"amount": "1.00"}, format="json")
        self.assertEqual(overpay.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_statement_charges_and_deposits(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        items_url = reverse("invoice-add-item", args=[invoice["id"]])
        self.client.post(
            items_url,
            {"service": self.fixed_service.id},
            format="json",
        )
        self.client.post(
            reverse("invoice-confirm", args=[invoice["id"]]),
            {"amount_paid": "30.00"},
            format="json",
        )

        deposit_url = reverse("client-deposits", args=[self.client_obj.id])
        deposit = self.client.post(
            deposit_url, {"amount": "20.00", "notes": "cash"}, format="json"
        )
        self.assertEqual(deposit.status_code, status.HTTP_201_CREATED, deposit.data)
        self.assertEqual(deposit.data["total_charged"], "100.00")
        self.assertEqual(deposit.data["total_deposits"], "50.00")
        self.assertEqual(deposit.data["balance_due"], "50.00")
        self.assertEqual(len(deposit.data["invoices"]), 1)
        self.assertEqual(len(deposit.data["deposits"]), 2)

        statement_url = reverse("client-statement", args=[self.client_obj.id])
        statement = self.client.get(statement_url)
        self.assertEqual(statement.status_code, status.HTTP_200_OK)
        self.assertEqual(statement.data["balance_due"], "50.00")
        self.assertEqual(statement.data["invoices"][0]["amount_remaining"], "70.00")

    def test_add_piece_with_multiple_services_and_quantity(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        pieces_url = reverse("invoice-add-piece", args=[invoice["id"]])
        response = self.client.post(
            pieces_url,
            {
                "length": "300.000",
                "width": "200.000",
                "quantity": "2",
                "items": [
                    {"service": self.one_dim_service.id, "unit_price": "10.00"},
                    {"service": self.two_dim_service.id, "unit_price": "5.00"},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(len(response.data["pieces"]), 1)
        piece = response.data["pieces"][0]
        # one_dim: 10 * (300*200/10000 = 6 m2) = 60; two_dim: 5 * 2*(300+200)/100 = 50
        self.assertEqual(piece["piece_subtotal"], "110.00")
        self.assertEqual(piece["piece_total"], "220.00")
        self.assertEqual(len(piece["items"]), 2)
        self.assertEqual(response.data["subtotal"], "220.00")
        self.assertEqual(response.data["total"], "220.00")
        self.assertEqual(len(response.data["items"]), 2)

    def test_add_piece_with_manual_measure_ignores_dimensions(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        response = self.client.post(
            reverse("invoice-add-piece", args=[invoice["id"]]),
            {
                "quantity": "3",
                "items": [
                    {
                        "service": self.two_dim_service.id,
                        "unit_price": "80.00",
                        "measure": "30",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        piece = response.data["pieces"][0]
        self.assertEqual(piece["items"][0]["measure"], "30.000")
        self.assertEqual(piece["piece_subtotal"], "2400.00")
        self.assertEqual(piece["piece_total"], "7200.00")

    def test_add_service_to_existing_piece(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        items_url = reverse("invoice-add-item", args=[invoice["id"]])
        created = self.client.post(
            items_url,
            {
                "service": self.one_dim_service.id,
                "length": "300.000",
                "width": "200.000",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        piece_id = created.data["pieces"][0]["id"]
        added = self.client.post(
            items_url,
            {
                "service": self.two_dim_service.id,
                "piece": piece_id,
            },
            format="json",
        )
        self.assertEqual(added.status_code, status.HTTP_201_CREATED, added.data)
        self.assertEqual(len(added.data["pieces"]), 1)
        self.assertEqual(len(added.data["pieces"][0]["items"]), 2)
        self.assertEqual(added.data["pieces"][0]["piece_subtotal"], "110.00")
        self.assertEqual(added.data["total"], "110.00")

    def test_update_piece_dimensions_recalculates_services(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        pieces_url = reverse("invoice-add-piece", args=[invoice["id"]])
        created = self.client.post(
            pieces_url,
            {
                "length": "300.000",
                "width": "200.000",
                "items": [
                    {"service": self.one_dim_service.id},
                    {"service": self.two_dim_service.id},
                ],
            },
            format="json",
        )
        piece_id = created.data["pieces"][0]["id"]
        piece_url = reverse("invoice-piece-detail", args=[invoice["id"], piece_id])
        updated = self.client.patch(
            piece_url,
            {"length": "400.000", "width": "100.000"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK, updated.data)
        piece = updated.data["pieces"][0]
        # one_dim: 10 * (400*100/10000 = 4 m2) = 40; two_dim: 5 * 2*(4+1) = 50
        self.assertEqual(piece["piece_subtotal"], "90.00")
        self.assertEqual(updated.data["total"], "90.00")

    def test_delete_last_item_removes_piece(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        items_url = reverse("invoice-add-item", args=[invoice["id"]])
        created = self.client.post(
            items_url,
            {"service": self.fixed_service.id},
            format="json",
        )
        item_id = created.data["items"][0]["id"]
        item_url = reverse("invoice-item-detail", args=[invoice["id"], item_id])
        deleted = self.client.delete(item_url)
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        self.assertEqual(deleted.data["items"], [])
        self.assertEqual(deleted.data["pieces"], [])
        self.assertEqual(deleted.data["total"], "0.00")

    def test_piece_requires_at_least_one_service(self) -> None:
        self.authenticate()
        invoice = self.create_draft()
        pieces_url = reverse("invoice-add-piece", args=[invoice["id"]])
        response = self.client.post(
            pieces_url,
            {"length": "300.000", "width": "200.000", "items": []},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class InvoiceDateFilterTests(InvoiceApiTests):
    def _numbers(self, **params) -> set[str]:
        response = self.client.get(self.list_url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return {row["number"] for row in response.data["results"]}

    def test_filter_by_issue_date_range(self) -> None:
        self.authenticate()
        old = self.create_draft(issue_date="2026-01-10")["number"]
        mid = self.create_draft(issue_date="2026-02-15")["number"]
        new = self.create_draft(issue_date="2026-03-20")["number"]

        self.assertEqual(self._numbers(issue_date_from="2026-02-01"), {mid, new})
        self.assertEqual(self._numbers(issue_date_to="2026-02-28"), {old, mid})
        self.assertEqual(
            self._numbers(issue_date_from="2026-02-01", issue_date_to="2026-02-28"),
            {mid},
        )
        # bounds are inclusive
        self.assertEqual(
            self._numbers(issue_date_from="2026-02-15", issue_date_to="2026-02-15"),
            {mid},
        )
        self.assertEqual(self._numbers(issue_date="2026-03-20"), {new})


class InvoicePrintTests(APITestCase):
    def setUp(self) -> None:
        user = User.objects.create_user(username="printer", password="pass12345")
        self.client.force_authenticate(user=user)
        self.client_obj = Client.objects.create(name="Ali", phone="01000000009")
        category = ServiceCategory.objects.create(name="Glass")
        self.qty = Service.objects.create(
            name="Qty",
            service_category=category,
            cost=Decimal("25.00"),
            cost_method=Service.CostMethod.QUANTITY,
        )

    def _invoice_with_items(self, n: int = 2) -> dict:
        created = self.client.post(
            reverse("invoice-list"), {"client": self.client_obj.id}, format="json"
        ).data
        for _ in range(n):
            self.client.post(
                reverse("invoice-add-item", args=[created["id"]]),
                {"service": self.qty.id, "quantity": "2"},
                format="json",
            )
        return created

    def _item_ids(self, invoice_id: int) -> list[int]:
        data = self.client.get(reverse("invoice-detail", args=[invoice_id])).data
        return [i["id"] for i in data["items"]]

    def test_print_sets_printed_at_once(self) -> None:
        inv = self._invoice_with_items()
        url = reverse("invoice-print-invoice", args=[inv["id"]])
        first = self.client.post(url)
        self.assertEqual(first.status_code, status.HTTP_200_OK, first.data)
        stamp = first.data["printed_at"]
        self.assertIsNotNone(stamp)
        second = self.client.post(url)
        self.assertEqual(second.data["printed_at"], stamp)

    def test_printed_invoice_blocks_item_delete(self) -> None:
        inv = self._invoice_with_items()
        item_id = self._item_ids(inv["id"])[0]
        self.client.post(reverse("invoice-print-invoice", args=[inv["id"]]))
        resp = self.client.delete(
            reverse("invoice-item-detail", args=[inv["id"], item_id])
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unprinted_confirmed_invoice_allows_item_delete(self) -> None:
        inv = self._invoice_with_items()
        self.client.post(reverse("invoice-confirm", args=[inv["id"]]), {}, format="json")
        item_id = self._item_ids(inv["id"])[0]
        resp = self.client.delete(
            reverse("invoice-item-detail", args=[inv["id"], item_id])
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["total"], "50.00")

    def test_confirmed_delete_rejected_when_payment_exceeds_new_total(self) -> None:
        inv = self._invoice_with_items()
        self.client.post(
            reverse("invoice-confirm", args=[inv["id"]]),
            {"amount_paid": "100.00"},
            format="json",
        )
        item_id = self._item_ids(inv["id"])[0]
        resp = self.client.delete(
            reverse("invoice-item-detail", args=[inv["id"], item_id])
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(self._item_ids(inv["id"])), 2)

    def _patch(self, inv_id: int, data: dict):
        return self.client.patch(
            reverse("invoice-detail", args=[inv_id]), data, format="json"
        )

    def test_confirmed_unpaid_unprinted_allows_discount(self) -> None:
        inv = self._invoice_with_items()
        self.client.post(reverse("invoice-confirm", args=[inv["id"]]), {}, format="json")
        resp = self._patch(inv["id"], {"discount_amount": "20.00"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["discount_amount"], "20.00")
        self.assertEqual(resp.data["total"], "80.00")

    def test_confirmed_discount_blocked_when_printed_or_paid(self) -> None:
        inv = self._invoice_with_items()
        self.client.post(
            reverse("invoice-confirm", args=[inv["id"]]),
            {"amount_paid": "10.00"},
            format="json",
        )
        self.assertEqual(
            self._patch(inv["id"], {"discount_amount": "5"}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        inv2 = self._invoice_with_items()
        self.client.post(reverse("invoice-confirm", args=[inv2["id"]]), {}, format="json")
        self.client.post(reverse("invoice-print-invoice", args=[inv2["id"]]))
        self.assertEqual(
            self._patch(inv2["id"], {"discount_amount": "5"}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_confirmed_other_header_fields_still_blocked(self) -> None:
        inv = self._invoice_with_items()
        self.client.post(reverse("invoice-confirm", args=[inv["id"]]), {}, format="json")
        resp = self._patch(inv["id"], {"notes": "x", "discount_amount": "5"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_removing_last_item_cancels_discount(self) -> None:
        inv = self._invoice_with_items()
        self._patch(inv["id"], {"discount_amount": "20.00"})
        for item_id in self._item_ids(inv["id"]):
            resp = self.client.delete(
                reverse("invoice-item-detail", args=[inv["id"], item_id])
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["discount_amount"], "0.00")
        self.assertEqual(resp.data["total"], "0.00")

    def test_removing_item_keeps_discount_when_it_still_fits(self) -> None:
        inv = self._invoice_with_items()
        self._patch(inv["id"], {"discount_amount": "20.00"})
        resp = self.client.delete(
            reverse("invoice-item-detail", args=[inv["id"], self._item_ids(inv["id"])[0]])
        )
        self.assertEqual(resp.data["discount_amount"], "20.00")


class DepositAutoSettleTests(InvoicePrintTests):
    def _confirmed(self) -> dict:
        inv = self._invoice_with_items()
        self.client.post(reverse("invoice-confirm", args=[inv["id"]]), {}, format="json")
        return inv

    def _deposit(self, amount: str):
        return self.client.post(
            reverse("client-deposits", args=[self.client_obj.id]),
            {"amount": amount},
            format="json",
        )

    def test_deposit_covering_last_invoice_settles_it(self) -> None:
        inv = self._confirmed()  # total 100
        self.assertEqual(self._deposit("120").status_code, status.HTTP_201_CREATED)
        got = Invoice.objects.get(pk=inv["id"])
        self.assertTrue(got.is_settled)
        self.assertEqual(got.amount_paid, Decimal("100.00"))
        self.assertEqual(got.payments.count(), 1)
        # excess 20 stays as client credit (standalone deposit)
        self.assertEqual(self.client_obj.payments.count(), 2)

    def test_exact_amount_settles(self) -> None:
        inv = self._confirmed()
        self._deposit("100")
        self.assertTrue(Invoice.objects.get(pk=inv["id"]).is_settled)

    def test_excess_of_50_or_more_stays_plain_deposit(self) -> None:
        inv = self._confirmed()
        self._deposit("150")
        self.assertFalse(Invoice.objects.get(pk=inv["id"]).is_settled)

    def test_smaller_amount_stays_plain_deposit(self) -> None:
        inv = self._confirmed()
        self._deposit("60")
        self.assertFalse(Invoice.objects.get(pk=inv["id"]).is_settled)


class PaymentMethodTests(InvoicePrintTests):
    """Reuses InvoicePrintTests.setUp helpers (own tests only below)."""

    def _confirmed(self, paid: str | None = None) -> dict:
        inv = self._invoice_with_items()  # total 100.00
        body = {"amount_paid": paid} if paid else {}
        resp = self.client.post(
            reverse("invoice-confirm", args=[inv["id"]]), body, format="json"
        )
        return resp.data

    def test_deposit_method_and_invoice_link(self) -> None:
        inv = self._confirmed()
        url = reverse("client-deposits", args=[self.client_obj.id])
        ok = self.client.post(
            url,
            {"amount": "40.00", "method": "instapay", "invoice": inv["id"]},
            format="json",
        )
        self.assertEqual(ok.status_code, status.HTTP_201_CREATED, ok.data)
        self.assertEqual(ok.data["deposits"][0]["method"], "instapay")
        self.assertEqual(ok.data["deposits"][0]["invoice"], inv["id"])
        detail = self.client.get(reverse("invoice-detail", args=[inv["id"]])).data
        self.assertEqual(detail["amount_paid"], "40.00")

    def test_deposit_cannot_exceed_invoice_remaining(self) -> None:
        inv = self._confirmed(paid="70.00")
        url = reverse("client-deposits", args=[self.client_obj.id])
        bad = self.client.post(
            url, {"amount": "31.00", "invoice": inv["id"]}, format="json"
        )
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        good = self.client.post(
            url, {"amount": "30.00", "invoice": inv["id"]}, format="json"
        )
        self.assertEqual(good.status_code, status.HTTP_201_CREATED)

    def test_deposit_invoice_must_belong_to_client(self) -> None:
        inv = self._confirmed()
        other = Client.objects.create(name="Other", phone="01099999999")
        resp = self.client.post(
            reverse("client-deposits", args=[other.id]),
            {"amount": "10.00", "invoice": inv["id"]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_method_rejected_and_default_cash(self) -> None:
        url = reverse("client-deposits", args=[self.client_obj.id])
        bad = self.client.post(url, {"amount": "5", "method": "bitcoin"}, format="json")
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        ok = self.client.post(url, {"amount": "5"}, format="json")
        self.assertEqual(ok.data["deposits"][0]["method"], "cash")

    def test_pay_endpoint_records_method(self) -> None:
        inv = self._confirmed()
        resp = self.client.post(
            reverse("invoice-pay", args=[inv["id"]]),
            {"amount": "20.00", "method": "wallet"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        from apps.invoices.models import Payment

        self.assertEqual(Payment.objects.get(invoice_id=inv["id"]).method, "wallet")


class PaymentListTests(APITestCase):
    def setUp(self) -> None:
        user = User.objects.create_user(username="cashier", password="pass12345")
        self.client.force_authenticate(user=user)
        self.a = Client.objects.create(name="A", phone="01000000101")
        self.b = Client.objects.create(name="B", phone="01000000102")
        self.url = reverse("payment-list")
        for client, amount, method, day in [
            (self.a, "10.00", "cash", "2026-03-01"),
            (self.a, "20.00", "instapay", "2026-03-15"),
            (self.b, "5.00", "wallet", "2026-04-01"),
        ]:
            self.client.post(
                reverse("client-deposits", args=[client.id]),
                {"amount": amount, "method": method, "paid_at": day},
                format="json",
            )

    def test_requires_auth(self) -> None:
        self.client.force_authenticate(user=None)
        self.assertEqual(
            self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_filters_and_summary(self) -> None:
        all_rows = self.client.get(self.url).data
        self.assertEqual(all_rows["count"], 3)
        self.assertEqual(all_rows["results"][0]["client_name"], "B")  # newest first

        by_client = self.client.get(self.url, {"client": self.a.id}).data
        self.assertEqual(by_client["count"], 2)

        ranged = self.client.get(
            self.url, {"start_date": "2026-03-10", "end_date": "2026-03-31"}
        ).data
        self.assertEqual([r["amount"] for r in ranged["results"]], ["20.00"])

        summary = self.client.get(
            reverse("payment-summary"), {"client": self.a.id}
        ).data
        self.assertEqual(summary["total_payments"], Decimal("30.00"))
        self.assertEqual(summary["count"], 2)
        self.assertEqual({r["method"] for r in summary["by_method"]}, {"cash", "instapay"})
