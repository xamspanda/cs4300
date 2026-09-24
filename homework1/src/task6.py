"""Task 6: Count whitespace-separated words in a UTF-8 text file."""

from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "task6_read_me.txt"


def count_words(file_path=DEFAULT_FILE):
    """Read a file one line at a time and count words.

    Whitespace separates words; attached punctuation stays with a word.
    File and encoding errors propagate so callers can identify the problem.
    The context manager closes the file even if reading fails.
    """
    with Path(file_path).open(encoding="utf-8") as text_file:
        return sum(len(line.split()) for line in text_file)


def main():
    """Print the supplied file's word count."""
    print(f"Word count: {count_words()}")


if __name__ == "__main__":
    main()
