"""Task 5: Store books in a list and student IDs in a dictionary."""

# Favorite books; all student names and IDs below are fictional.
favorite_books = [
    {"title": "Fablehaven", "author": "Brandon Mull"},
    {"title": "Fablehaven: Rise of the Evening Star", "author": "Brandon Mull"},
    {"title": "Fablehaven: Grip of the Shadow Plague", "author": "Brandon Mull"},
    {"title": "House of Leaves", "author": "Mark Z. Danielewski"},
]

students = {"Alex Rivera": "S001", "Sam Chen": "S002", "Jordan Lee": "S003"}


def first_three_books(books):
    """Use slicing to return up to three books without changing the list."""
    return books[:3]


def print_first_three_books(books):
    """Display the title and author of each selected book."""
    for book in first_three_books(books):
        print(f"{book['title']} by {book['author']}")


def student_id(name):
    """Look up a student's ID; an unknown name raises KeyError."""
    return students[name]


if __name__ == "__main__":
    print_first_three_books(favorite_books)
    print(f"Alex Rivera: {student_id('Alex Rivera')}")
