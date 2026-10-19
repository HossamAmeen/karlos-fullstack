from django.contrib.auth import get_user_model
from pathlib import Path
from unittest import mock

from django.test import TestCase
from rest_framework.test import APIClient


class BackupTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username="s", password="p", is_staff=True)
        self.user = User.objects.create_user(username="u", password="p")

    def test_requires_staff(self):
        client = APIClient()
        client.force_authenticate(self.user)
        assert client.post("/api/v1/backups/").status_code == 403

    def test_admin_button_requires_login(self):
        resp = self.client.post("/admin/backup/")
        assert resp.status_code == 302 and "login" in resp.url

    def test_staff_creates_backup(self):
        client = APIClient()
        client.force_authenticate(self.staff)
        with mock.patch("apps.core.backup.celery_available", return_value=False), \
                mock.patch("apps.core.backup.create_backup", return_value=Path("b.sqlite3")):
            resp = client.post("/api/v1/backups/")
        assert resp.status_code == 201
        assert resp.json() == {"mode": "sync", "file": "b.sqlite3"}

    def test_uses_celery_when_available(self):
        client = APIClient()
        client.force_authenticate(self.staff)
        with mock.patch("apps.core.backup.celery_available", return_value=True), \
                mock.patch("apps.core.tasks.backup_database.delay") as delay:
            delay.return_value.id = "abc"
            resp = client.post("/api/v1/backups/")
        assert resp.status_code == 202
        assert resp.json() == {"mode": "celery", "task_id": "abc"}

    def test_celery_unavailable_without_config(self):
        from apps.core.backup import celery_available

        with self.settings(CELERY_CONFIGURED=False):
            assert celery_available() is False
