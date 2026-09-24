"""Check branches, prime boundaries, printed output, and the sum."""

import pytest

from task3 import classify_number, first_ten_primes, is_prime, print_first_ten_primes, sum_to_100


@pytest.mark.parametrize("number, expected", [
    (10, "positive"), (-10, "negative"), (0, "zero"),
    (0.5, "positive"), (-0.5, "negative"), (-0.0, "zero"),
])
def test_sign(number, expected):
    assert classify_number(number) == expected


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_sign(number):
    with pytest.raises(ValueError, match="finite"):
        classify_number(number)


@pytest.mark.parametrize("number, expected", [
    (-7, False), (0, False), (1, False), (2, True), (3, True),
    (4, False), (9, False), (25, False), (29, True), (49, False), (97, True),
])
def test_primality(number, expected):
    assert is_prime(number) is expected


def test_first_ten_primes():
    assert first_ten_primes() == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def test_print_primes(capsys):
    print_first_ten_primes()
    assert capsys.readouterr().out == "2\n3\n5\n7\n11\n13\n17\n19\n23\n29\n"


def test_sum():
    assert sum_to_100() == 5050
