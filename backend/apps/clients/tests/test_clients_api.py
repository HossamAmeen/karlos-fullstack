from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.clients.models import Client

User = get_user_model()


class ClientApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="staff", password="staffpass123")
        self.list_url = reverse("client-list")

    def authenticate(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_requires_authentication(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_list_update_delete_client(self) -> None:
        self.authenticate()

        create_response = self.client.post(
            self.list_url,
            {
                "name": "Acme Glass",
                "phone": "+201000000000",
                "email": "info@acme.example",
                "address": "Cairo",
                "note": "VIP",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        client_id = create_response.data["id"]

        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)

        detail_url = reverse("client-detail", args=[client_id])
        update_response = self.client.patch(
            detail_url,
            {"note": "Updated"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["note"], "Updated")

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Client.objects.filter(pk=client_id).exists())

    def test_phone_must_be_unique_among_active_clients(self) -> None:
        self.authenticate()
        payload = {
            "name": "Acme Glass",
            "phone": "+201000000000",
            "email": "info@acme.example",
        }
        first = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        duplicate = self.client.post(
            self.list_url,
            {**payload, "name": "Other Glass"},
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", duplicate.data)

        detail_url = reverse("client-detail", args=[first.data["id"]])
        self.assertEqual(
            self.client.delete(detail_url).status_code,
            status.HTTP_204_NO_CONTENT,
        )

        reuse = self.client.post(
            self.list_url,
            {**payload, "name": "Reused Phone"},
            format="json",
        )
        self.assertEqual(reuse.status_code, status.HTTP_201_CREATED)
