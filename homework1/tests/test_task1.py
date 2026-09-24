"""Verify the greeting when called and when run as a script."""

import runpy

import task1


def test_greeting(capsys):
    task1.main()
    assert capsys.readouterr().out == "Hello, World!\n"


def test_script(capsys):
    runpy.run_path(task1.__file__, run_name="__main__")
    assert capsys.readouterr().out == "Hello, World!\n"
