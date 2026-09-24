"""Check book slicing, output, and dictionary lookups."""

import pytest

from task5 import favorite_books, first_three_books, print_first_three_books, student_id, students


def test_book_data():
    assert len(favorite_books) >= 4
    for book in favorite_books:
        assert set(book) == {"title", "author"}
        assert all(isinstance(value, str) and value for value in book.values())


@pytest.mark.parametrize("books, expected", [
    ([], []), (["A"], ["A"]), (["A", "B"], ["A", "B"]),
    (["A", "B", "C"], ["A", "B", "C"]),
    (["A", "B", "C", "D"], ["A", "B", "C"]),
])
def test_slicing(books, expected):
    original = books.copy()
    result = first_three_books(books)
    assert result == expected
    assert result is not books
    assert books == original


def test_print_books(capsys):
    books = [
        {"title": "First", "author": "A"}, {"title": "Second", "author": "B"},
        {"title": "Third", "author": "C"}, {"title": "Fourth", "author": "D"},
    ]
    print_first_three_books(books)
    assert capsys.readouterr().out == "First by A\nSecond by B\nThird by C\n"


@pytest.mark.parametrize("name, expected", [
    ("Alex Rivera", "S001"), ("Sam Chen", "S002"), ("Jordan Lee", "S003"),
])
def test_student_lookup(name, expected):
    assert student_id(name) == expected


def test_unknown_student():
    with pytest.raises(KeyError):
        student_id("Unknown Student")


def test_unique_student_ids():
    assert len(set(students.values())) == len(students)
