"""Task 3: Make decisions and repeat work with for and while loops."""

from math import isfinite, isqrt


def classify_number(number):
    """Return the sign of a finite real number."""
    if not isfinite(number):
        raise ValueError("number must be finite")
    if number > 0:
        return "positive"
    elif number < 0:
        return "negative"
    else:
        return "zero"


def is_prime(number):
    """Check an integer for divisors up to its square root."""
    if number < 2:
        return False
    for divisor in range(2, isqrt(number) + 1):
        if number % divisor == 0:
            return False
    return True


def first_ten_primes():
    """Return the first ten primes in order."""
    # The tenth prime is 29, so this range includes all ten candidates.
    return [number for number in range(2, 30) if is_prime(number)]


def print_first_ten_primes():
    """Use a for loop to print one prime per line."""
    for number in first_ten_primes():
        print(number)


def sum_to_100():
    """Use a while loop to add the integers from 1 through 100."""
    total = 0
    number = 1
    while number <= 100:
        total += number
        number += 1
    return total


def main():
    """Demonstrate all three control structures."""
    print(f"Sign of -7: {classify_number(-7)}")
    print_first_ten_primes()
    print(f"Sum from 1 to 100: {sum_to_100()}")


if __name__ == "__main__":
    main()
