"""Task 2: Use integers, floating-point numbers, strings, and booleans."""

quantity = 3
unit_price = 12.50
product_name = "Notebook"
in_stock = True


def describe_product():
    """Use each data type in a small product summary."""
    return {
        "next_quantity": quantity + 1,
        "total_price": quantity * unit_price,
        "label": product_name.upper(),
        "can_order": in_stock and quantity > 0,
    }


def main():
    """Display the values and their derived results."""
    for name, value in describe_product().items():
        print(f"{name}: {value}")


if __name__ == "__main__":
    main()
