"""Check NumPy results with known datasets and invalid data."""

import numpy as np
import pytest

from task7 import summarize_measurements


@pytest.mark.parametrize("values, mean, minimum, maximum", [
    ([18.5, 20.0, 21.5, 24.0], 21.0, 18.5, 24.0),
    ([1, 2, 3], 2.0, 1.0, 3.0), ([5], 5.0, 5.0, 5.0),
    ([-5, -1, 0], -2.0, -5.0, 0.0), ([0, 0], 0.0, 0.0, 0.0),
])
def test_summary(values, mean, minimum, maximum):
    original = values.copy()
    assert summarize_measurements(values) == pytest.approx({
        "mean": mean, "minimum": minimum, "maximum": maximum,
    })
    assert values == original


def test_numpy_array():
    assert summarize_measurements(np.array([2, 4, 6])) == {
        "mean": 4.0, "minimum": 2.0, "maximum": 6.0,
    }


@pytest.mark.parametrize("values", [[], [[1, 2]], 3, [float("nan")], [float("inf")], [-float("inf")]])
def test_invalid_shape_or_values(values):
    with pytest.raises(ValueError):
        summarize_measurements(values)


def test_nonnumeric_data():
    with pytest.raises(ValueError):
        summarize_measurements(["not a number"])
