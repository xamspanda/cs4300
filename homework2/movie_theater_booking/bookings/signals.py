"""Signal handlers for the bookings app."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Booking, Movie
from .services import create_seats_for_movie, refresh_seat_status


@receiver(post_save, sender=Movie)
def add_seats_to_new_movie(sender, instance, created, raw=False, **kwargs):
    """Every new movie comes with its seats, however it was created (002 AC-13).

    raw is True while loading fixtures, which bring their own seats.
    """
    if created and not raw:
        create_seats_for_movie(instance)


@receiver(post_delete, sender=Booking)
def free_seat_of_deleted_booking(sender, instance, **kwargs):
    """Keep the seat's status right however a booking is deleted: cancelling,
    the admin site, or a cascade such as deleting the user (002 §7)."""
    refresh_seat_status(instance.seat_id)
