"""API viewsets and HTML page views for the bookings app."""

from itertools import groupby
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from rest_framework import exceptions, mixins, status, viewsets
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


class BookingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """The signed-in user's bookings at /api/bookings/ (003).

    list, retrieve, create and destroy (cancel) only. There is no update, so PUT
    and PATCH are 405 (AC-10).
    """

    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Every action looks bookings up through this, so another user's
        # booking is simply not found: 404, never 403 (AC-2, AC-3).
        return self.request.user.bookings.select_related("movie", "seat")

    def create(self, request, *args, **kwargs):
        """Book {"seat": id} for the signed-in user: 201, 400, 401 or 409 (AC-7)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return book_seat_response(request.user, serializer.validated_data["seat"])

    def perform_destroy(self, instance):
        services.cancel_booking(instance)  # AC-9


def movie_list(request):
    """The home page: every movie with a Book Now button (001 AC-1 to AC-3)."""
    return render(request, "bookings/movie_list.html", {"movies": Movie.objects.all()})


@require_http_methods(["GET", "POST"])
def seat_booking(request, movie_id):
    """Show a movie's seats (GET) and book one for the signed-in user (POST) (002).

    POST always redirects back here (post/redirect/get), so refreshing the page
    never resubmits a booking. The outcome is shown as a flash message.
    """
    movie = get_object_or_404(Movie, pk=movie_id)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect_to_login(request.path)  # AC-8
        seat = movie.seats.filter(pk=_int_or_none(request.POST.get("seat"))).first()
        if seat is None:
            messages.error(request, "That seat does not exist for this movie.")  # AC-9
        else:
            try:
                services.book_seat(request.user, seat)
                messages.success(request, f"You booked seat {seat.seat_number} for {movie}.")
            except services.SeatUnavailable as error:
                messages.error(request, str(error))  # AC-3
        return redirect("book_seat", movie_id=movie.pk)

    seats = movie.seats.all()
    my_seat_ids = set()
    if request.user.is_authenticated:
        my_seat_ids = set(
            request.user.bookings.filter(movie=movie).values_list("seat_id", flat=True)
        )
    context = {
        "movie": movie,
        "seats": seats,
        "rows": [(row, list(group)) for row, group in groupby(seats, key=attrgetter("row"))],
        "available_count": sum(not s.is_booked for s in seats),
        "my_seat_ids": my_seat_ids,
    }
    return render(request, "bookings/seat_booking.html", context)


@login_required
def booking_history(request):
    """My Bookings: the signed-in user's bookings, newest first (003)."""
    bookings = request.user.bookings.select_related("movie", "seat")
    return render(request, "bookings/booking_history.html", {"bookings": bookings})


@login_required
@require_POST
def cancel_booking(request, booking_id):
    """Cancel one of the signed-in user's bookings (003 AC-9).

    POST only, so a link or a prefetch can never cancel a booking. Looking the
    booking up among the user's own makes anyone else's a 404.
    """
    booking = get_object_or_404(
        request.user.bookings.select_related("movie", "seat"), pk=booking_id
    )
    services.cancel_booking(booking)
    messages.success(
        request,
        f"Cancelled your booking of seat {booking.seat.seat_number} for {booking.movie}.",
    )
    return redirect("booking_history")


def _int_or_none(value):
    """Turn form input into an id, or None if it isn't a whole number."""
    return int(value) if value and value.isdigit() else None


def signup(request):
    """Create an account and sign straight in (002 AC-14)."""
    if request.user.is_authenticated:
        return redirect("movie_list")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        return redirect("movie_list")
    return render(request, "registration/signup.html", {"form": form})
