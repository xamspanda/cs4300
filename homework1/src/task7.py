"""Task 7: Use NumPy to summarize a set of numeric measurements."""

import numpy as np


def summarize_measurements(values):
    """Return mean, minimum, and maximum for finite, one-dimensional data."""
    measurements = np.asarray(values, dtype=float)
    if measurements.ndim != 1 or measurements.size == 0:
        raise ValueError("provide a nonempty, one-dimensional set of measurements")
    if not np.isfinite(measurements).all():
        raise ValueError("measurements must all be finite")
    return {
        "mean": float(np.mean(measurements)),
        "minimum": float(np.min(measurements)),
        "maximum": float(np.max(measurements)),
    }


if __name__ == "__main__":
    print(summarize_measurements([18.5, 20.0, 21.5, 24.0]))
