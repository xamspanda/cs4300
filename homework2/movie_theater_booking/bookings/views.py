"""API viewsets and HTML page views for the bookings app."""

from django.shortcuts import render
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import Movie, Seat
from .serializers import BookingSerializer, MovieSerializer, SeatSerializer


class SeatConflict(exceptions.APIException):
    """409: the request was valid, but the seat is already booked (002 AC-3)."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "seat_unavailable"


def book_seat_response(user, seat):
    """Book through the shared service and answer 201, or 409 if the seat is taken."""
    try:
        booking = services.book_seat(user, seat)
    except services.SeatUnavailable as error:
        raise SeatConflict(str(error)) from None
    return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class MovieViewSet(viewsets.ModelViewSet):
    """CRUD for movies at /api/movies/ (001). Anyone reads; signed-in users write."""

    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


class SeatViewSet(viewsets.ReadOnlyModelViewSet):
    """Seat availability at /api/seats/, plus POST /api/seats/<id>/book/ (002).

    Read-only, so creating, editing or deleting seats is 405 (AC-12).
    Filters: ?movie=<id> and ?booking_status=available|booked (AC-10).
    """

    serializer_class = SeatSerializer

    def get_queryset(self):
        seats = Seat.objects.all()
        movie = self.request.query_params.get("movie")
        if movie is not None:
            if not movie.isdigit():
                raise exceptions.ValidationError({"movie": "Must be a whole-number movie id."})
            seats = seats.filter(movie_id=int(movie))
        booking_status = self.request.query_params.get("booking_status")
        if booking_status:
            seats = seats.filter(booking_status=booking_status)
        return seats

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def book(self, request, pk=None):
        """Book this seat for the signed-in user: 201, 401, 404 or 409 (AC-11)."""
        return book_seat_response(request.user, self.get_object())


def movie_list(request):
    """The home page: every movie with a Book Now button (001 AC-1 to AC-3)."""
    return render(request, "bookings/movie_list.html", {"movies": Movie.objects.all()})
