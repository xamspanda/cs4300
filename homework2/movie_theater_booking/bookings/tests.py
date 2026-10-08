"""Unit and integration tests for the bookings app.

Each test class follows one feature spec in specs/, and each test names the
acceptance criterion (AC-#) it proves in its docstring.
"""

from datetime import date

from django.test import TestCase

from .models import Movie


def make_movie(title="Dune", release_date=date(2021, 10, 22), duration=155, **kwargs):
    """Create a movie with sensible defaults for tests."""
    return Movie.objects.create(
        title=title, release_date=release_date, duration=duration, **kwargs
    )


class MovieModelTests(TestCase):
    """001 — Data rules for Movie."""

    def test_movie_str_and_ordering(self):
        """A movie prints as its title, and movies list newest release first."""
        older = make_movie("Up", date(2009, 5, 29), 96)
        newer = make_movie("Dune", date(2021, 10, 22), 155)
        self.assertEqual(str(newer), "Dune")
        self.assertEqual(list(Movie.objects.all()), [newer, older])
