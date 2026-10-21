from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.services.models import Service

TWO = Decimal("0.01")
CM_PER_METER = Decimal("100")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(TWO)


def compute_line_subtotal(
    *,
    cost_method: str,
    unit_price: Decimal,
    quantity: Decimal | None = None,
    length: Decimal | None = None,
    width: Decimal | None = None,
    measure: Decimal | None = None,
) -> Decimal:
    """Pure pricing engine - server source of truth for line amounts before item
    discount.

    ``length`` / ``width`` are in centimetres and converted to metres here;
    ``measure`` is already in metres.
    """
    if unit_price < 0:
        raise ValidationError({"unit_price": "Unit price must be >= 0."})

    if cost_method == Service.CostMethod.FIXED:
        return quantize_money(unit_price)

    if cost_method == Service.CostMethod.QUANTITY:
        if quantity is None:
            raise ValidationError(
                {"quantity": "Quantity is required for quantity pricing."}
            )
        if quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than 0."})
        return quantize_money(unit_price * quantity)

    is_dimensional = cost_method in (
        Service.CostMethod.ONE_DIMENSION,
        "area",
        Service.CostMethod.TWO_DIMENSIONS,
        "perimeter",
    )
    if is_dimensional and measure is not None:
        if measure < 0:
            raise ValidationError({"measure": "Measure must be >= 0."})
        return quantize_money(unit_price * measure)

    if cost_method in (Service.CostMethod.ONE_DIMENSION, "area"):
        dim = width if width is not None else length
        if dim is None:
            raise ValidationError(
                {"width": "Width is required for one dimension cost method."}
            )
        if dim < 0:
            raise ValidationError({"width": "Dimension must be >= 0."})
        dim = dim / CM_PER_METER
        measure = dim * dim
        return quantize_money(unit_price * measure)

    if cost_method in (Service.CostMethod.TWO_DIMENSIONS, "perimeter"):
        if length is None or width is None:
            raise ValidationError(
                {
                    "length": (
                        "Length and width are required for two dimensions cost method."
                    ),
                    "width": (
                        "Length and width are required for two dimensions cost method."
                    ),
                }
            )
        if length < 0 or width < 0:
            raise ValidationError(
                {
                    "length": "Length and width must be >= 0.",
                    "width": "Length and width must be >= 0.",
                }
            )
        measure = Decimal("2") * (length + width) / CM_PER_METER
        return quantize_money(unit_price * measure)

    raise ValidationError({"cost_method": f"Unsupported cost method: {cost_method}"})


def apply_discount(*, amount: Decimal, discount: Decimal, field: str) -> Decimal:
    if discount < 0:
        raise ValidationError({field: "Discount must be >= 0."})
    if discount > amount:
        raise ValidationError({field: "Discount cannot exceed the amount."})
    return quantize_money(amount - discount)
