"""Unit and integration tests for the bookings app.

Each test class follows one feature spec in specs/, and each test names the
acceptance criterion (AC-#) it proves in its docstring.
"""

from datetime import date
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from . import services
from .models import Booking, Movie, Seat

User = get_user_model()


def make_movie(title="Dune", release_date=date(2021, 10, 22), duration=155, **kwargs):
    """Create a movie with sensible defaults for tests."""
    return Movie.objects.create(
        title=title, release_date=release_date, duration=duration, **kwargs
    )


def make_user(username="sam", password="test-pass-123"):
    """Create a user; tests sign in with force_login / force_authenticate."""
    return User.objects.create_user(username=username, password=password)


class MovieModelTests(TestCase):
    """001 — Data rules for Movie."""

    def test_movie_str_and_ordering(self):
        """A movie prints as its title, and movies list newest release first."""
        older = make_movie("Up", date(2009, 5, 29), 96)
        newer = make_movie("Dune", date(2021, 10, 22), 155)
        self.assertEqual(str(newer), "Dune")
        self.assertEqual(list(Movie.objects.all()), [newer, older])


class MovieApiTests(APITestCase):
    """001 — /api/movies/ CRUD (AC-4 to AC-8, AC-10)."""

    def setUp(self):
        self.user = make_user()
        self.client.force_authenticate(self.user)
        self.list_url = reverse("movie-list")
        self.valid = {
            "title": "Arrival",
            "description": "Linguist meets aliens.",
            "release_date": "2016-11-11",
            "duration": 116,
        }

    def detail_url(self, movie):
        return reverse("movie-detail", args=[movie.pk])

    def test_list_movies(self):
        """AC-4: GET returns 200 and every movie with all of its fields."""
        make_movie("Dune")
        make_movie("Up", date(2009, 5, 29), 96)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            set(response.data[0]),
            {"id", "title", "description", "release_date", "duration"},
        )

    def test_create_movie(self):
        """AC-5: POST with valid data returns 201 and the movie is listed."""
        response = self.client.post(self.list_url, self.valid, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        titles = [m["title"] for m in self.client.get(self.list_url).data]
        self.assertIn("Arrival", titles)

    def assert_rejected(self, data, field):
        """POST data, expect 400 with an error for field, and nothing saved."""
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(field, response.data)
        self.assertFalse(Movie.objects.exists())

    def test_create_movie_missing_title_400(self):
        """AC-6: a missing title is rejected."""
        data = dict(self.valid)
        del data["title"]
        self.assert_rejected(data, "title")

    def test_create_movie_missing_release_date_400(self):
        """AC-6: a missing release date is rejected."""
        data = dict(self.valid)
        del data["release_date"]
        self.assert_rejected(data, "release_date")

    def test_create_movie_zero_duration_400(self):
        """AC-6: duration 0 (the boundary) and negative durations are rejected."""
        for duration in (0, -5):
            with self.subTest(duration=duration):
                self.assert_rejected(dict(self.valid, duration=duration), "duration")

    def test_create_movie_with_blank_description(self):
        """Data: description is optional."""
        data = dict(self.valid, description="")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_movie(self):
        """AC-8: GET one movie returns 200 with its fields."""
        dune = make_movie("Dune")
        response = self.client.get(self.detail_url(dune))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Dune")
        self.assertEqual(response.data["duration"], 155)
        self.assertEqual(response.data["release_date"], "2021-10-22")

    def test_get_missing_movie_404(self):
        """AC-8: a movie that doesn't exist is 404."""
        response = self.client.get(reverse("movie-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_movie(self):
        """AC-7: PUT and PATCH return 200 with the new values."""
        dune = make_movie("Dune")
        response = self.client.put(
            self.detail_url(dune), dict(self.valid, title="Dune: Part One"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Dune: Part One")
        response = self.client.patch(self.detail_url(dune), {"duration": 156}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dune.refresh_from_db()
        self.assertEqual(dune.duration, 156)

    def test_update_movie_invalid_400(self):
        """AC-7 / AC-6: an update with invalid data is 400 and changes nothing."""
        dune = make_movie("Dune")
        response = self.client.patch(self.detail_url(dune), {"duration": 0}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        dune.refresh_from_db()
        self.assertEqual(dune.duration, 155)

    def test_delete_movie(self):
        """AC-7: DELETE returns 204 and the movie is gone."""
        dune = make_movie("Dune")
        response = self.client.delete(self.detail_url(dune))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Movie.objects.filter(pk=dune.pk).exists())

    def test_anonymous_can_read_but_not_change_movies(self):
        """AC-10: anonymous GET is 200; POST, PATCH and DELETE are 401."""
        dune = make_movie("Dune")
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_200_OK)
        attempts = [
            self.client.post(self.list_url, self.valid, format="json"),
            self.client.patch(self.detail_url(dune), {"title": "X"}, format="json"),
            self.client.delete(self.detail_url(dune)),
        ]
        for response in attempts:
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        dune.refresh_from_db()
        self.assertEqual(dune.title, "Dune")
        self.assertEqual(Movie.objects.count(), 1)


class MovieListPageTests(TestCase):
    """001 — The movie list page (AC-1 to AC-3, AC-9)."""

    def test_movie_list_uses_base_template(self):
        """AC-9: the page extends base.html (Bootstrap) with a Movies link."""
        response = self.client.get(reverse("movie_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/movie_list.html")
        self.assertTemplateUsed(response, "bookings/base.html")
        self.assertContains(response, "bootstrap")
        self.assertContains(response, f'href="{reverse("movie_list")}"')

    def test_movie_list_shows_titles_descriptions_and_book_now(self):
        """AC-1: every movie appears with its description and a Book Now button."""
        make_movie("Dune", description="Desert planet.")
        make_movie("Up", date(2009, 5, 29), 96, description="Balloon house.")
        response = self.client.get(reverse("movie_list"))
        for text in ("Dune", "Desert planet.", "Up", "Balloon house."):
            self.assertContains(response, text)
        self.assertContains(response, "Book Now", count=2)

    def test_movie_list_shows_release_date_and_duration(self):
        """AC-3: release date and duration are readable."""
        make_movie("Dune", date(2021, 10, 22), 155)
        response = self.client.get(reverse("movie_list"))
        self.assertContains(response, "October 22, 2021")
        self.assertContains(response, "2h 35m")

    def test_movie_list_empty_state(self):
        """AC-2: with no movies, the page says so instead of showing an empty list."""
        response = self.client.get(reverse("movie_list"))
        self.assertContains(response, "No movies are showing right now")


class MovieDurationDisplayTests(TestCase):
    """001 AC-3 — duration_display, including boundaries."""

    def test_duration_display(self):
        cases = {155: "2h 35m", 120: "2h", 45: "45m", 1: "1m", 60: "1h"}
        for minutes, expected in cases.items():
            with self.subTest(minutes=minutes):
                self.assertEqual(Movie(duration=minutes).duration_display, expected)


# ---------------------------------------------------------------------------
# 002 — Seat booking
# ---------------------------------------------------------------------------


def seat(movie, number):
    """Look up one of a movie's automatically created seats, e.g. seat(dune, "A1")."""
    return movie.seats.get(seat_number=number)


class SeatModelTests(TestCase):
    """002 — Seat data rules and automatic seats (AC-13)."""

    def test_seat_str_and_default_status(self):
        """Data: a seat prints as "A1 – Dune" and starts available."""
        dune = make_movie("Dune")
        a1 = seat(dune, "A1")
        self.assertEqual(str(a1), "A1 – Dune")
        self.assertEqual(a1.booking_status, Seat.BookingStatus.AVAILABLE)
        self.assertFalse(a1.is_booked)

    def test_new_movie_gets_40_available_seats(self):
        """AC-13: a new movie has rows A–E with seats 1–8, all available."""
        dune = make_movie("Dune")
        numbers = [s.seat_number for s in dune.seats.all()]
        self.assertEqual(len(numbers), 40)
        self.assertEqual(numbers[:3], ["A1", "A2", "A3"])
        self.assertIn("E8", numbers)
        self.assertFalse(dune.seats.exclude(booking_status="available").exists())

    def test_updating_a_movie_does_not_add_seats(self):
        """AC-13: seats are made only when the movie is created."""
        dune = make_movie("Dune")
        dune.title = "Dune: Part One"
        dune.save()
        self.assertEqual(dune.seats.count(), 40)

    def test_seat_numbers_unique_within_a_movie(self):
        """Data: a movie can't have two A1 seats, but two movies each have their own A1."""
        dune = make_movie("Dune")
        up = make_movie("Up")
        self.assertEqual(Seat.objects.filter(seat_number="A1").count(), 2)
        # The savepoint keeps the test's transaction usable after the error.
        with self.assertRaises(IntegrityError), transaction.atomic():
            Seat.objects.create(movie=dune, seat_number="A1")
        self.assertEqual(up.seats.count(), 40)


class BookingModelTests(TestCase):
    """002 — Booking data rules (AC-4)."""

    def test_duplicate_booking_rejected_by_database(self):
        """AC-4: saving a second booking of a seat directly raises IntegrityError."""
        dune = make_movie("Dune")
        a1 = seat(dune, "A1")
        Booking.objects.create(movie=dune, seat=a1, user=make_user("sam"))
        alex = make_user("alex")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Booking.objects.create(movie=dune, seat=a1, user=alex)
        self.assertEqual(Booking.objects.count(), 1)

    def test_booking_str(self):
        """Data: a booking prints who booked which seat."""
        dune = make_movie("Dune")
        booking = Booking.objects.create(movie=dune, seat=seat(dune, "A1"), user=make_user())
        self.assertEqual(str(booking), "sam: A1 – Dune")


class BookSeatServiceTests(TestCase):
    """002 — The one shared booking operation (AC-2 to AC-4)."""

    def setUp(self):
        self.dune = make_movie("Dune")
        self.a1 = seat(self.dune, "A1")
        self.sam = make_user("sam")

    def test_book_seat_creates_booking_and_marks_seat_booked(self):
        """AC-2: booking saves movie, seat, user and date, and marks the seat booked."""
        booking = services.book_seat(self.sam, self.a1)
        self.assertEqual(booking.user, self.sam)
        self.assertEqual(booking.movie, self.dune)
        self.assertEqual(booking.seat, self.a1)
        self.assertIsNotNone(booking.booking_date)
        self.a1.refresh_from_db()
        self.assertTrue(self.a1.is_booked)

    def test_book_seat_refuses_taken_seat(self):
        """AC-3: a second booking of the same seat raises SeatUnavailable."""
        services.book_seat(self.sam, self.a1)
        with self.assertRaisesMessage(
            services.SeatUnavailable, "Seat A1 for Dune is already booked."
        ):
            services.book_seat(make_user("alex"), self.a1)
        self.assertEqual(Booking.objects.count(), 1)

    def test_book_seat_turns_integrity_error_into_seat_unavailable(self):
        """AC-4: a duplicate saved behind the service's back is still refused cleanly.

        The seat's stored status still says "available", which is exactly the
        race the database constraint exists for.
        """
        Booking.objects.create(movie=self.dune, seat=self.a1, user=self.sam)
        with self.assertRaises(services.SeatUnavailable):
            services.book_seat(make_user("alex"), self.a1)
        self.assertEqual(Booking.objects.count(), 1)

    def test_book_seat_leaves_other_movies_seats_alone(self):
        """Data: availability is per movie."""
        up = make_movie("Up")
        services.book_seat(self.sam, self.a1)
        self.assertFalse(seat(up, "A1").is_booked)
