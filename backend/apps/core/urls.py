from django.urls import path

from .views import HealthView, StatisticsView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
]

v1_urlpatterns = [
    path("statistics/", StatisticsView.as_view(), name="statistics"),
]
