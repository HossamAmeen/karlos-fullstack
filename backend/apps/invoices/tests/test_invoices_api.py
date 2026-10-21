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
                "width": "30.00",
                "unit_price": "10.00",
            },
            format="json",
        )
        self.assertEqual(one_dim.status_code, status.HTTP_201_CREATED, one_dim.data)
        # 10 * 3 * 3 = 90
        self.assertEqual(one_dim.data["items"][1]["line_total"], "90.00")
        self.assertEqual(one_dim.data["subtotal"], "180.00")

        qty = self.client.post(
            items_url,
            {"service": self.qty_service.id, "quantity": "4"},
            format="json",
        )
        self.assertEqual(qty.status_code, status.HTTP_201_CREATED, qty.data)
        self.assertEqual(qty.data["items"][2]["line_total"], "100.00")

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
        self.assertEqual(two_dim.data["subtotal"], "300.00")
        self.assertEqual(two_dim.data["total"], "300.00")

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
        # one_dim: 10 * (200*200/100 = 400 m) = 4000; two_dim: 5 * 2*(300+200)/100 = 50
        self.assertEqual(piece["piece_subtotal"], "4050.00")
        self.assertEqual(piece["piece_total"], "8100.00")
        self.assertEqual(len(piece["items"]), 2)
        self.assertEqual(response.data["subtotal"], "8100.00")
        self.assertEqual(response.data["total"], "8100.00")
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
        self.assertEqual(added.data["pieces"][0]["piece_subtotal"], "4050.00")
        self.assertEqual(added.data["total"], "4050.00")

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
        # one_dim: 10 * 1 * 1 = 10; two_dim: 5 * 2*(4+1) = 50
        self.assertEqual(piece["piece_subtotal"], "1050.00")
        self.assertEqual(updated.data["total"], "1050.00")

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
