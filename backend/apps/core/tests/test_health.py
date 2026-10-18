from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class HealthApiTests(APITestCase):
    def test_health_is_public(self) -> None:
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok", "database": "ok", "version": "2"})

    def test_health_reports_database_failure(self) -> None:
        with patch("apps.core.views.connection.cursor", side_effect=Exception("down")):
            response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
