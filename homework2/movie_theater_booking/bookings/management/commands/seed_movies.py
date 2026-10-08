"""python manage.py seed_movies — add sample movies so a fresh site isn't empty.

Safe to run more than once: a movie whose title already exists is skipped.
The Render build runs it after migrating.
"""

from datetime import date

from django.core.management.base import BaseCommand

from bookings.models import Movie

SAMPLE_MOVIES = [
    {
        "title": "Dune: Part Two",
        "description": "Paul Atreides unites with the Fremen while seeking revenge "
        "against those who destroyed his family.",
        "release_date": date(2024, 3, 1),
        "duration": 166,
    },
    {
        "title": "Inside Out 2",
        "description": "Riley's emotions face a crowd of new arrivals as she becomes a teenager.",
        "release_date": date(2024, 6, 14),
        "duration": 96,
    },
    {
        "title": "Spider-Man: Across the Spider-Verse",
        "description": "Miles Morales is catapulted across the Multiverse and meets "
        "a team of Spider-People.",
        "release_date": date(2023, 6, 2),
        "duration": 140,
    },
    {
        "title": "Arrival",
        "description": "A linguist works to talk with alien visitors before "
        "tensions on Earth boil over.",
        "release_date": date(2016, 11, 11),
        "duration": 116,
    },
    {
        "title": "Up",
        "description": "A retired balloon salesman ties thousands of balloons to his "
        "house and flies to South America.",
        "release_date": date(2009, 5, 29),
        "duration": 96,
    },
]


class Command(BaseCommand):
    help = "Add sample movies (each gets its 40 seats automatically)."

    def handle(self, *args, **options):
        added = 0
        for movie in SAMPLE_MOVIES:
            _, created = Movie.objects.get_or_create(title=movie["title"], defaults=movie)
            added += created
        self.stdout.write(self.style.SUCCESS(f"Sample movies: {added} added."))
