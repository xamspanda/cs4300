"""Serializers that turn the bookings models into JSON for the REST API."""

from rest_framework import serializers

from .models import Booking, Movie, Seat


class MovieSerializer(serializers.ModelSerializer):
    """A movie; the model's validators reject a duration of 0 or less (001 AC-6)."""

    class Meta:
        model = Movie
        fields = ["id", "title", "description", "release_date", "duration"]


class SeatSerializer(serializers.ModelSerializer):
    """A seat and whether it is booked. Read-only: seats change only by booking (002 AC-12)."""

    class Meta:
        model = Seat
        fields = ["id", "movie", "seat_number", "booking_status"]
        read_only_fields = fields


class BookingSerializer(serializers.ModelSerializer):
    """A booking. Clients choose only the seat; the server sets everything else.

    user is read-only, so a "user" value in the request is ignored and the view
    supplies request.user instead (002 AC-5). movie is always the seat's movie.
    """

    movie_title = serializers.CharField(source="movie.title", read_only=True)
    seat_number = serializers.CharField(source="seat.seat_number", read_only=True)
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "movie", "movie_title", "seat", "seat_number", "user", "booking_date"]
        read_only_fields = ["movie", "booking_date"]
        # DRF would turn the one-booking-per-seat constraint into a 400 "already
        # exists" check. Leave that decision to services.book_seat, so a taken
        # seat is the same 409 on every route (002 AC-6).
        extra_kwargs = {"seat": {"validators": []}}
