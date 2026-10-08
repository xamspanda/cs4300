"""Signal handlers for the bookings app."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Movie
from .services import create_seats_for_movie


@receiver(post_save, sender=Movie)
def add_seats_to_new_movie(sender, instance, created, raw=False, **kwargs):
    """Every new movie comes with its seats, however it was created (002 AC-13).

    raw is True while loading fixtures, which bring their own seats.
    """
    if created and not raw:
        create_seats_for_movie(instance)
