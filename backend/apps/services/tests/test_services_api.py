from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.services.models import Service, ServiceCategory

User = get_user_model()


class ServiceCategoryApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="staff", password="staffpass123")
        self.list_url = reverse("service-category-list")

    def authenticate(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_requires_authentication(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_list_update_delete_category(self) -> None:
        self.authenticate()

        create_response = self.client.post(
            self.list_url,
            {"name": "Installation"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        category_id = create_response.data["id"]

        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)

        detail_url = reverse("service-category-detail", args=[category_id])
        update_response = self.client.patch(
            detail_url,
            {"name": "Repair"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["name"], "Repair")

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ServiceCategory.objects.filter(pk=category_id).exists())

    def test_name_must_be_unique_among_active_categories(self) -> None:
        self.authenticate()
        payload = {"name": "Installation"}
        first = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        duplicate = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", duplicate.data)

        detail_url = reverse("service-category-detail", args=[first.data["id"]])
        self.assertEqual(
            self.client.delete(detail_url).status_code,
            status.HTTP_204_NO_CONTENT,
        )

        reuse = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(reuse.status_code, status.HTTP_201_CREATED)


class ServiceApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="staff2", password="staffpass123")
        self.list_url = reverse("service-list")
        self.category = ServiceCategory.objects.create(name="Installation")

    def authenticate(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_requires_authentication(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_list_update_delete_service(self) -> None:
        self.authenticate()

        create_response = self.client.post(
            self.list_url,
            {
                "name": "Window install",
                "service_category": self.category.id,
                "cost": "150.00",
                "cost_method": "two_dimensions",
                "is_fixed_cost": True,
                "is_additional_service": False,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["service_category_name"], "Installation")
        self.assertEqual(create_response.data["cost_method"], "two_dimensions")
        service_id = create_response.data["id"]

        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)

        detail_url = reverse("service-detail", args=[service_id])
        update_response = self.client.patch(
            detail_url,
            {
                "cost": "175.50",
                "cost_method": "one_dimension",
                "is_additional_service": True,
            },
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["cost"], "175.50")
        self.assertEqual(update_response.data["cost_method"], "one_dimension")
        self.assertTrue(update_response.data["is_additional_service"])

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Service.objects.filter(pk=service_id).exists())

    def test_cost_cannot_be_negative(self) -> None:
        self.authenticate()
        response = self.client.post(
            self.list_url,
            {
                "name": "Bad cost",
                "service_category": self.category.id,
                "cost": "-1.00",
                "cost_method": "two_dimensions",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cost", response.data)

    def test_cost_method_must_be_valid(self) -> None:
        self.authenticate()
        response = self.client.post(
            self.list_url,
            {
                "name": "Bad method",
                "service_category": self.category.id,
                "cost": "10.00",
                "cost_method": "volume",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cost_method", response.data)

    def test_filter_by_service_category(self) -> None:
        self.authenticate()
        other = ServiceCategory.objects.create(name="Delivery")
        Service.objects.create(
            name="Install A",
            service_category=self.category,
            cost="10.00",
            cost_method=Service.CostMethod.TWO_DIMENSIONS,
        )
        Service.objects.create(
            name="Deliver B",
            service_category=other,
            cost="20.00",
            cost_method=Service.CostMethod.ONE_DIMENSION,
        )

        response = self.client.get(
            self.list_url,
            {"service_category": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Install A")
