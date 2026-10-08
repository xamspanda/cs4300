"""Data models for the movie theater: movies, their seats, and bookings."""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Movie(models.Model):
    """A movie the theater is showing (spec 001)."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    release_date = models.DateField()
    # PositiveIntegerField still allows 0, and a zero-minute movie is not valid.
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], help_text="Length in whole minutes."
    )

    class Meta:
        ordering = ["-release_date"]

    def __str__(self):
        return self.title

    @property
    def duration_display(self):
        """Duration as hours and minutes, e.g. 155 -> "2h 35m" (001 AC-3)."""
        hours, minutes = divmod(self.duration, 60)
        parts = [f"{hours}h"] if hours else []
        if minutes or not hours:
            parts.append(f"{minutes}m")
        return " ".join(parts)


class Seat(models.Model):
    """One seat for one movie (spec 002).

    Each movie has its own seats, so availability is per movie. The Booking
    table is the source of truth for whether a seat is taken; booking_status is
    a copy that only bookings/services.py writes, in the same transaction.
    """

    class BookingStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        BOOKED = "booked", "Booked"

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=3, help_text="Row letter and number, e.g. A1.")
    booking_status = models.CharField(
        max_length=10, choices=BookingStatus.choices, default=BookingStatus.AVAILABLE
    )

    class Meta:
        ordering = ["movie", "seat_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["movie", "seat_number"], name="unique_seat_number_per_movie"
            )
        ]

    def __str__(self):
        return f"{self.seat_number} – {self.movie}"

    @property
    def is_booked(self):
        return self.booking_status == self.BookingStatus.BOOKED

    @property
    def row(self):
        """The row letter, used to lay the seats out in rows on the page."""
        return self.seat_number[0]


class Booking(models.Model):
    """A user's reservation of one seat (specs 002 and 003)."""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="bookings")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    booking_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Newest first; id breaks ties between bookings made in the same instant.
        ordering = ["-booking_date", "-id"]
        constraints = [
            # The database, not a check in Python, is what stops two
            # simultaneous requests from booking the same seat (002 AC-4).
            models.UniqueConstraint(fields=["seat"], name="one_booking_per_seat")
        ]

    def __str__(self):
        return f"{self.user}: {self.seat}"
