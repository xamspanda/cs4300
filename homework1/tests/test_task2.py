"""Check each data type and the operation that uses it."""

import pytest

import task2


@pytest.mark.parametrize("name, expected_type, expected", [
    ("quantity", int, 3),
    ("unit_price", float, 12.5),
    ("product_name", str, "Notebook"),
    ("in_stock", bool, True),
])
def test_data_types(name, expected_type, expected):
    value = getattr(task2, name)
    # Exact types distinguish bool from int, since bool subclasses int.
    assert type(value) is expected_type
    assert value == expected


@pytest.mark.parametrize("key, expected", [
    ("next_quantity", 4),
    ("total_price", 37.5),
    ("label", "NOTEBOOK"),
    ("can_order", True),
])
def test_operations(key, expected):
    assert task2.describe_product()[key] == expected
