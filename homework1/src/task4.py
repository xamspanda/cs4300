"""Task 4: Calculate a discounted price using numeric operations."""

from math import isfinite


def calculate_discount(price, discount):
    """Return price less discount percent, without rounding.

    Inputs must be finite real numeric values with compatible arithmetic.
    Price must be nonnegative; discount must be in [0, 100]. Integers,
    floats, Decimal, and Fraction work without converting them to float.
    Python's normal rules apply to mixed types (Decimal + float is invalid).
    """
    for name, value in (("price", price), ("discount", discount)):
        if isinstance(value, bool):
            raise TypeError(f"{name} must be numeric, not a boolean")
        # Calling numeric operations, rather than requiring a concrete class,
        # lets compatible numeric types supply their own behavior.
        if not isfinite(value):
            raise ValueError(f"{name} must be finite")
    if price < 0:
        raise ValueError("price must be nonnegative")
    if not 0 <= discount <= 100:
        raise ValueError("discount must be between 0 and 100")
    return price - price * discount / 100


if __name__ == "__main__":
    print(f"Discounted price: {calculate_discount(80, 25)}")
