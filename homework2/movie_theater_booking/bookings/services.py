"""The booking rules, in one place (spec 002 AC-6).

The seat booking page, /api/seats/<id>/book/ and /api/bookings/ all call
book_seat(), so a seat can never be taken through one route while another
route would refuse it.
"""

from django.db import IntegrityError, transaction

from .models import Booking, Seat

SEAT_ROWS = "ABCDE"
SEATS_PER_ROW = 8


class SeatUnavailable(Exception):
    """Raised when a seat already has a booking."""

    def __init__(self, seat):
        self.seat = seat
        super().__init__(f"Seat {seat.seat_number} for {seat.movie} is already booked.")


def create_seats_for_movie(movie):
    """Give a new movie its seats: rows A–E, numbers 1–8 (002 AC-13)."""
    Seat.objects.bulk_create(
        Seat(movie=movie, seat_number=f"{row}{number}")
        for row in SEAT_ROWS
        for number in range(1, SEATS_PER_ROW + 1)
    )


@transaction.atomic
def book_seat(user, seat):
    """Book seat for user and mark it booked; raise SeatUnavailable if it is taken.

    There is deliberately no "is it free?" check before saving: two requests
    could both pass it. The unique constraint on Booking.seat decides, and its
    IntegrityError becomes the same SeatUnavailable a taken seat gives (AC-4).
    """
    # Lock the seat row until the transaction ends (PostgreSQL; SQLite locks
    # the whole database on write instead).
    seat = Seat.objects.select_for_update().select_related("movie").get(pk=seat.pk)
    try:
        # A savepoint, so the failed insert doesn't break the outer transaction.
        with transaction.atomic():
            booking = Booking.objects.create(user=user, seat=seat, movie=seat.movie)
    except IntegrityError:
        raise SeatUnavailable(seat) from None
    seat.booking_status = Seat.BookingStatus.BOOKED
    seat.save(update_fields=["booking_status"])
    return booking
