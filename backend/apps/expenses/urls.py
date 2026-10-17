from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r"expense-main-categories",
    views.ExpenseMainCategoryViewSet,
    basename="expense-main-category",
)
router.register(
    r"expense-categories", views.ExpenseCategoryViewSet, basename="expense-category"
)
router.register(r"expenses", views.ExpenseViewSet, basename="expense")

urlpatterns = [
    path("", include(router.urls)),
]
