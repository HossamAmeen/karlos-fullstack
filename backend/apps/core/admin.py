from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path

from .backup import BackupError, run_backup


def backup_view(request):
    if not request.user.is_active or not request.user.is_staff:
        return redirect("admin:login")
    if request.method == "POST":
        try:
            result = run_backup()
        except BackupError as exc:
            messages.error(request, f"Backup failed: {exc}")
        else:
            if result["mode"] == "celery":
                messages.success(request, f"Backup queued (task {result['task_id']})")
            else:
                messages.success(request, f"Backup created: {result['file']}")
    return redirect("admin:index")


_original_get_urls = admin.site.get_urls


def _get_urls():
    return [
        path("backup/", admin.site.admin_view(backup_view), name="backup"),
        *_original_get_urls(),
    ]


admin.site.get_urls = _get_urls  # type: ignore[method-assign]
