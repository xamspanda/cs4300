"""Check multiple real temporary files and file-system failures."""

import pytest

from task6 import count_words


@pytest.mark.parametrize("text, expected", [
    ("", 0), (" \n\t ", 0), ("hello", 1), ("one two three", 3),
    ("one\n two\tthree  four", 4), ("Hello, world!", 2),
    ("café naïve 日本語", 3), ("one\r\ntwo\r\n", 2),
])
def test_text_files(tmp_path, text, expected):
    path = tmp_path / "sample.txt"
    path.write_text(text, encoding="utf-8")
    assert count_words(path) == expected
    assert count_words(str(path)) == expected


def test_supplied_file():
    assert count_words() == 104


def test_default_path_does_not_depend_on_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert count_words() == 104


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        count_words(tmp_path / "missing.txt")


def test_directory(tmp_path):
    with pytest.raises(IsADirectoryError):
        count_words(tmp_path)


def test_invalid_utf8(tmp_path):
    path = tmp_path / "invalid.txt"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(UnicodeDecodeError):
        count_words(path)
