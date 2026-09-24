"""Check numeric duck typing, percentage boundaries, and invalid inputs."""

from decimal import Decimal
from fractions import Fraction

import pytest

from task4 import calculate_discount


@pytest.mark.parametrize("price, discount, expected", [
    (100, 20, 80), (100.0, 20, 80.0), (100, 12.5, 87.5),
    (19.99, 15.0, 16.9915), (100, 0, 100), (100, 100, 0), (0, 25, 0),
])
def test_integer_and_float_inputs(price, discount, expected):
    assert calculate_discount(price, discount) == pytest.approx(expected)


@pytest.mark.parametrize("price, discount, expected", [
    (Decimal("19.99"), Decimal("15"), Decimal("16.9915")),
    (Decimal("20"), 25, Decimal("15")),
    (20, Decimal("25"), Decimal("15")),
    (Fraction(100, 3), Fraction(25), Fraction(25)),
    (Fraction(20), 25, Fraction(15)),
])
def test_other_numeric_types(price, discount, expected):
    result = calculate_discount(price, discount)
    assert result == expected
    assert type(result) is type(expected)


@pytest.mark.parametrize("price, discount", [(-1, 10), (10, -1), (10, 101)])
def test_invalid_ranges(price, discount):
    with pytest.raises(ValueError):
        calculate_discount(price, discount)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), Decimal("NaN")])
@pytest.mark.parametrize("field", ["price", "discount"])
def test_nonfinite_inputs(bad, field):
    arguments = {"price": 100, "discount": 10}
    arguments[field] = bad
    with pytest.raises(ValueError, match="finite"):
        calculate_discount(**arguments)


@pytest.mark.parametrize("bad", ["100", None, [], 1 + 2j, True, False])
@pytest.mark.parametrize("field", ["price", "discount"])
def test_nonnumeric_inputs(bad, field):
    arguments = {"price": 100, "discount": 10}
    arguments[field] = bad
    with pytest.raises(TypeError):
        calculate_discount(**arguments)


def test_incompatible_numeric_types():
    with pytest.raises(TypeError):
        calculate_discount(Decimal("100"), 10.5)
