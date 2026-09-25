# Homework 1: Introduction to Python and Unit Testing

## Setup and execution

Requires Python 3.12 or newer. Run the following commands from the
repository root (for example, `/coursework/cs4300` in DevEDU):

```bash
cd homework1
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pytest
```

The virtual environment must be activated again in each new terminal.
`requirements.txt` pins the two direct dependencies, NumPy and pytest.
Homework 1 uses its own virtual environment, separate from other assignments.

Run one task or all seven demonstrations from the `homework1` directory:

```bash
python3 src/task1.py
for task in src/task[1-7].py; do python3 "$task"; done
```

## Tasks and explanations

1. **Output.** `main()` prints `Hello, World!`. The main guard runs the
   demonstration only when the file is executed. Importing the module does not
   print. Tests use pytest's `capsys` fixture to inspect standard output, including
   the final newline. A second test runs the actual script entry point.

2. **Variables and types.** A quantity is an `int`, a unit price is a `float`,
   the product name is a `str`, and stock availability is a `bool`. The summary
   uses addition, multiplication, a string method, and a Boolean expression.
   Parameterized tests check each value, exact type, and computed result.
   Exact type checks matter here because Python treats `bool` as a subclass of
   `int`.

3. **Control structures.** `if`/`elif`/`else` selects the number's sign.
   Primality testing looks for a divisor from 2 through the integer square root:
   a composite number must have at least one factor in that range. Values below
   2 are not prime. A `for` loop prints `2, 3, 5, 7, 11, 13, 17, 19, 23, 29`,
   one per line. A `while` loop accumulates 1 through 100, producing **5050**.
   Tests cover zero, both signs, fractional values, nonfinite values, 0/1,
   primes, composites, and perfect squares.

4. **Functions and duck typing.** `calculate_discount(price, discount)` computes
   `price - price * discount / 100`. It uses the inputs' numeric operations;
   it does not force all inputs to be floats or require one numeric class.
   Compatible `int`, `float`, `Decimal`, and `Fraction` values are tested.
   Prices must be finite and nonnegative; percentages must be finite and from
   0 through 100. Booleans and nonnumeric objects are rejected. Python's ordinary
   arithmetic compatibility rules still apply: a `Decimal` and a `float` cannot
   be multiplied directly. Complex numbers cannot represent an ordered price.
   The function returns an unrounded result; floating-point tests use
   `pytest.approx`, while Decimal and Fraction tests check exact results.

5. **Lists and dictionaries.** The ordered book list contains title/author
   dictionaries. `books[:3]` creates a list containing up to the first three
   entries. The original list is unchanged. A separate dictionary maps fictional
   student names to student IDs. Direct lookup raises `KeyError` for an unknown
   student. Tests cover empty, short, exact-length, and longer lists, printed
   titles/authors, known and unknown students, and unique IDs.

6. **File handling.** The supplied Lorem ipsum text contains **104 words**.
   A word is a whitespace-separated token; punctuation attached to a word does
   not add another word. The file is read line by line as UTF-8 inside a `with`
   block, which closes it even when an error occurs. The default path is based
   on the module's location so the working directory does not matter. Missing
   files, directory paths, and invalid UTF-8 produce their normal exceptions
   rather than silently reporting zero. Parameterized tests create real temporary
   files with empty text, varied whitespace, punctuation, and Unicode.

7. **Package management.** NumPy computes the mean, minimum, and maximum of
   sample temperature measurements. `[18.5, 20.0, 21.5, 24.0]` produces a mean of
   **21.0**, a minimum of **18.5**, and a maximum of **24.0**. Conversion to an
   array enables NumPy's numeric operations. Empty, multidimensional, and
   nonfinite data are rejected. Tests use known datasets and need no network
   calls or mocks.

## Structure

```text
homework1/
  src/task1.py ... task7.py
  tests/test_task1.py ... test_task7.py
  task6_read_me.txt
  requirements.txt
  pyproject.toml
  README.md
homework2/
  .gitkeep
```

The pytest configuration adds `src/` to the import path and selects `tests/`.
Each test has an expected result independent of the implementation.
The `@pytest.mark.parametrize` decorators generate test cases from tables.

## References and assistance

- [Assignment](https://tghastings.github.io/cs4300andcs5300/homework_1.pdf)
- [pytest parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html)
- [Python Decimal arithmetic](https://docs.python.org/3/library/decimal.html)
- [NumPy mean](https://numpy.org/doc/stable/reference/generated/numpy.mean.html)
- [Brandon Mull's Fablehaven books](https://brandonmull.com/category/fablehaven/)
- [Mark Z. Danielewski's books](https://www.markzdanielewski.com/books-new)

Codex assisted with implementation, test design, and these explanations.
