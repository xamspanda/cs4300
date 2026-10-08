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


def refresh_seat_status(seat_id):
    """Copy the truth (does a booking exist?) into the seat's stored status.

    Every change to bookings ends here, including cascades such as deleting a
    user (see signals.py), so the stored status can't drift from the bookings.
    """
    booked = Booking.objects.filter(seat_id=seat_id).exists()
    status = Seat.BookingStatus.BOOKED if booked else Seat.BookingStatus.AVAILABLE
    Seat.objects.filter(pk=seat_id).update(booking_status=status)


def book_seat(user, seat):
    """Book seat for user and mark it booked; raise SeatUnavailable if it is taken.

    There is deliberately no "is it free?" check before saving: two requests
    could both pass it. The unique constraint on Booking.seat decides, and its
    IntegrityError becomes the same SeatUnavailable a taken seat gives (AC-4).
    """
    with transaction.atomic():
        # Lock the seat row until the transaction ends (PostgreSQL; SQLite
        # locks the whole database for the transaction instead).
        seat = Seat.objects.select_for_update().select_related("movie").get(pk=seat.pk)
        try:
            # A savepoint, so the failed insert doesn't break the outer transaction.
            with transaction.atomic():
                booking = Booking.objects.create(user=user, seat=seat, movie=seat.movie)
        except IntegrityError:
            booking = None
        # Also repairs a stale "available" when the database refused a duplicate.
        refresh_seat_status(seat.pk)
    # Raised after the transaction commits, so the repaired status is kept.
    if booking is None:
        raise SeatUnavailable(seat)
    return booking


@transaction.atomic
def cancel_booking(booking):
    """Delete a booking; its seat becomes available again (003 AC-9).

    Callers must check the booking belongs to the user asking; the API and the
    page do that by only ever looking up the signed-in user's bookings.
    Deleting by id means a repeated (stale) cancel deletes nothing, rather than
    freeing a seat someone else has booked since.
    """
    Seat.objects.select_for_update().filter(pk=booking.seat_id).exists()  # lock the seat
    Booking.objects.filter(pk=booking.pk, seat_id=booking.seat_id).delete()
    refresh_seat_status(booking.seat_id)
