from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.services.models import Service
from apps.services.pricing import apply_discount, compute_line_subtotal


@pytest.mark.parametrize(
    ("method", "unit_price", "quantity", "length", "width", "expected"),
    [
        (Service.CostMethod.FIXED, "100.00", None, None, None, Decimal("100.00")),
        (Service.CostMethod.QUANTITY, "10.00", "3", None, None, Decimal("30.00")),
        (Service.CostMethod.TWO_DIMENSIONS, "5.00", None, "200", "300", Decimal("50.00")),
        (Service.CostMethod.ONE_DIMENSION, "4.00", None, None, "500", Decimal("10.00")),
    ],
)
def test_compute_line_subtotal(
    method, unit_price, quantity, length, width, expected
) -> None:
    result = compute_line_subtotal(
        cost_method=method,
        unit_price=Decimal(unit_price),
        quantity=None if quantity is None else Decimal(quantity),
        length=None if length is None else Decimal(length),
        width=None if width is None else Decimal(width),
    )
    assert result == expected


def test_quantity_requires_positive_quantity() -> None:
    with pytest.raises(ValidationError):
        compute_line_subtotal(
            cost_method=Service.CostMethod.QUANTITY,
            unit_price=Decimal("10"),
            quantity=Decimal("0"),
        )


def test_discount_cannot_exceed_amount() -> None:
    with pytest.raises(ValidationError):
        apply_discount(
            amount=Decimal("10.00"),
            discount=Decimal("11.00"),
            field="discount_amount",
        )


def test_apply_discount_ok() -> None:
    assert apply_discount(
        amount=Decimal("10.00"),
        discount=Decimal("2.50"),
        field="discount_amount",
    ) == Decimal("7.50")
