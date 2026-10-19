from django.urls import path

from .views import BackupView, HealthView, StatisticsView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
]

v1_urlpatterns = [
    path("backups/", BackupView.as_view(), name="backups"),
    path("statistics/", StatisticsView.as_view(), name="statistics"),
]
