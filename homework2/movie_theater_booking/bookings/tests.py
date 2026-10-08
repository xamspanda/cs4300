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
from django.utils import timezone
from django.utils.dateformat import format as format_date
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


class SeatApiTests(APITestCase):
    """002 — /api/seats/ availability and booking (AC-3 to AC-5, AC-8 to AC-12)."""

    def setUp(self):
        self.dune = make_movie("Dune")
        self.up = make_movie("Up", date(2009, 5, 29), 96)
        self.sam = make_user("sam")
        self.alex = make_user("alex")
        self.a1 = seat(self.dune, "A1")
        self.a2 = seat(self.dune, "A2")
        services.book_seat(self.alex, self.a2)
        self.client.force_authenticate(self.sam)

    def book_url(self, seat_obj_or_id):
        pk = getattr(seat_obj_or_id, "pk", seat_obj_or_id)
        return reverse("seat-book", args=[pk])

    def test_list_seats_filtered_by_movie(self):
        """AC-10: ?movie= returns only that movie's seats, with their status."""
        response = self.client.get(reverse("seat-list"), {"movie": self.dune.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 40)
        self.assertEqual({s["movie"] for s in response.data}, {self.dune.pk})
        first = response.data[0]
        self.assertEqual(set(first), {"id", "movie", "seat_number", "booking_status"})
        by_number = {s["seat_number"]: s["booking_status"] for s in response.data}
        self.assertEqual(by_number["A2"], "booked")
        self.assertEqual(by_number["A1"], "available")

    def test_list_seats_unfiltered_includes_every_movie(self):
        """AC-10: without filters, every movie's seats are listed."""
        response = self.client.get(reverse("seat-list"))
        self.assertEqual(len(response.data), 80)

    def test_list_seats_filtered_by_status(self):
        """AC-10: &booking_status=available leaves booked seats out."""
        response = self.client.get(
            reverse("seat-list"), {"movie": self.dune.pk, "booking_status": "available"}
        )
        numbers = [s["seat_number"] for s in response.data]
        self.assertEqual(len(numbers), 39)
        self.assertNotIn("A2", numbers)

    def test_list_seats_bad_movie_param_400(self):
        """AC-10: a movie id that isn't a whole number is 400."""
        response = self.client.get(reverse("seat-list"), {"movie": "dune"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_seat_and_missing_seat(self):
        """AC-10 / AC-9: one seat is 200; a missing one is 404."""
        response = self.client.get(reverse("seat-detail", args=[self.a2.pk]))
        self.assertEqual(response.data["booking_status"], "booked")
        response = self.client.get(reverse("seat-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_seats_can_be_read_anonymously(self):
        """AC-10 / AC-8: anyone can check availability."""
        self.client.force_authenticate(None)
        response = self.client.get(reverse("seat-list"), {"movie": self.dune.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_seats_cannot_be_changed_via_api(self):
        """AC-12: create, update and delete are 405 and change nothing."""
        detail = reverse("seat-detail", args=[self.a1.pk])
        attempts = [
            self.client.post(
                reverse("seat-list"),
                {"movie": self.dune.pk, "seat_number": "Z9"},
                format="json",
            ),
            self.client.put(detail, {"booking_status": "booked"}, format="json"),
            self.client.patch(detail, {"booking_status": "booked"}, format="json"),
            self.client.delete(detail),
        ]
        for response in attempts:
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.a1.refresh_from_db()
        self.assertFalse(self.a1.is_booked)
        self.assertEqual(Seat.objects.count(), 80)

    def test_book_seat_via_seats_api(self):
        """AC-11: POST book returns 201 with the booking, and the seat is booked."""
        response = self.client.post(self.book_url(self.a1))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["seat"], self.a1.pk)
        self.assertEqual(response.data["seat_number"], "A1")
        self.assertEqual(response.data["movie"], self.dune.pk)
        self.assertEqual(response.data["movie_title"], "Dune")
        self.assertEqual(response.data["user"], "sam")
        self.assertIn("booking_date", response.data)
        self.a1.refresh_from_db()
        self.assertTrue(self.a1.is_booked)

    def test_booking_user_is_request_user_not_request_data(self):
        """AC-5: a user named in the request data is ignored."""
        response = self.client.post(
            self.book_url(self.a1), {"user": self.alex.pk}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.get(seat=self.a1).user, self.sam)

    def test_book_taken_seat_via_api_409(self):
        """AC-3: booking a taken seat is 409 with the reason, and nothing is saved."""
        response = self.client.post(self.book_url(self.a2))
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["detail"], "Seat A2 for Dune is already booked.")
        self.assertEqual(Booking.objects.get(seat=self.a2).user, self.alex)

    def test_duplicate_booking_returns_error_not_500(self):
        """AC-4: even when the stored status is stale, the database refusal becomes 409."""
        Booking.objects.create(movie=self.dune, seat=self.a1, user=self.alex)
        response = self.client.post(self.book_url(self.a1))
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_book_missing_seat_api_404(self):
        """AC-9: booking a seat that doesn't exist is 404."""
        response = self.client.post(self.book_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_api_booking_401(self):
        """AC-8: booking without signing in is 401 and saves nothing."""
        self.client.force_authenticate(None)
        response = self.client.post(self.book_url(self.a1))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Booking.objects.filter(seat=self.a1).exists())


class AccountPageTests(TestCase):
    """002 AC-14 — Sign up, sign in and sign out."""

    password = "Popcorn-and-Soda-42"

    def signup(self, username, password1=None, password2=None):
        return self.client.post(
            reverse("signup"),
            {
                "username": username,
                "password1": password1 or self.password,
                "password2": password2 or self.password,
            },
        )

    def test_signup_signs_in_and_redirects(self):
        """AC-14: a new account is signed in and returned to the movie list."""
        response = self.signup("taylor")
        self.assertRedirects(response, reverse("movie_list"))
        self.assertTrue(User.objects.filter(username="taylor").exists())
        page = self.client.get(reverse("movie_list"))
        self.assertTrue(page.wsgi_request.user.is_authenticated)
        self.assertContains(page, "taylor")
        self.assertContains(page, "Sign out")

    def test_signup_page_renders(self):
        """AC-14: the sign-up form is shown with the site layout."""
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/base.html")

    def test_signup_rejects_taken_username_and_mismatch(self):
        """AC-14: a taken username or mismatched passwords show an error and make no account."""
        make_user("sam")
        response = self.signup("sam")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        response = self.signup("riley", password2="Something-Else-99")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "didn’t match")
        self.assertEqual(User.objects.count(), 1)

    def test_signed_in_user_visiting_signup_is_redirected(self):
        """AC-14: there's no reason to sign up while signed in."""
        self.client.force_login(make_user("sam"))
        self.assertRedirects(self.client.get(reverse("signup")), reverse("movie_list"))

    def test_sign_out_and_in_again(self):
        """AC-14: sign out, then sign in with the same username and password."""
        self.signup("taylor")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("movie_list"))
        page = self.client.get(reverse("movie_list"))
        self.assertFalse(page.wsgi_request.user.is_authenticated)
        self.assertContains(page, "Sign in")
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        response = self.client.post(
            reverse("login"), {"username": "taylor", "password": self.password}
        )
        self.assertRedirects(response, reverse("movie_list"))


class SeatBookingPageTests(TestCase):
    """002 — The seat booking page (AC-1 to AC-3, AC-5 to AC-9)."""

    def setUp(self):
        self.dune = make_movie("Dune")
        self.sam = make_user("sam")
        self.alex = make_user("alex")
        self.a1 = seat(self.dune, "A1")
        self.a2 = seat(self.dune, "A2")
        services.book_seat(self.alex, self.a2)
        self.url = reverse("book_seat", args=[self.dune.pk])

    def test_movie_list_book_now_links_to_seat_page(self):
        """AC-1: "Book Now" on the movie list links to the movie's seat page."""
        response = self.client.get(reverse("movie_list"))
        self.assertContains(response, f'href="{self.url}"')

    def test_seat_page_shows_booked_and_available_seats(self):
        """AC-1: booked seats are shown unavailable, the rest available."""
        self.client.force_login(self.sam)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dune")
        seats = {s.seat_number: s for s in response.context["seats"]}
        self.assertTrue(seats["A2"].is_booked)
        self.assertFalse(seats["A1"].is_booked)
        # A free seat is a submit button; a booked seat's button is disabled.
        self.assertContains(response, f'name="seat" value="{self.a1.pk}"')
        self.assertContains(response, 'aria-label="Seat A2, booked" disabled')
        self.assertEqual(len(response.context["rows"]), 5)

    def test_seat_booking_uses_base_template(self):
        """AC-7: the page extends base.html with the same navbar."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "bookings/seat_booking.html")
        self.assertTemplateUsed(response, "bookings/base.html")

    def test_seat_page_missing_movie_404(self):
        """AC-9: the seat page for a movie that doesn't exist is 404."""
        response = self.client.get(reverse("book_seat", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_book_seat_via_page(self):
        """AC-2: booking a free seat confirms it and shows it as taken."""
        self.client.force_login(self.sam)
        response = self.client.post(self.url, {"seat": self.a1.pk}, follow=True)
        self.assertRedirects(response, self.url)
        self.assertContains(response, "You booked seat A1 for Dune.")
        self.assertContains(response, 'aria-label="Seat A1, booked" disabled')
        self.a1.refresh_from_db()
        self.assertTrue(self.a1.is_booked)

    def test_page_booking_user_is_request_user(self):
        """AC-5: the booking belongs to the signed-in user, whatever the form says."""
        self.client.force_login(self.sam)
        self.client.post(self.url, {"seat": self.a1.pk, "user": self.alex.pk})
        self.assertEqual(Booking.objects.get(seat=self.a1).user, self.sam)

    def test_book_taken_seat_via_page_shows_error(self):
        """AC-3: a taken seat shows the reason and saves nothing."""
        self.client.force_login(self.sam)
        response = self.client.post(self.url, {"seat": self.a2.pk}, follow=True)
        self.assertContains(response, "Seat A2 for Dune is already booked.")
        self.assertEqual(Booking.objects.get(seat=self.a2).user, self.alex)

    def test_book_other_movies_seat_via_page_refused(self):
        """AC-9: a seat id from another movie, or none at all, books nothing."""
        up = make_movie("Up", date(2009, 5, 29), 96)
        self.client.force_login(self.sam)
        for data in ({"seat": seat(up, "A1").pk}, {"seat": "9999"}, {"seat": "x"}, {}):
            with self.subTest(data=data):
                response = self.client.post(self.url, data, follow=True)
                self.assertContains(response, "That seat does not exist for this movie.")
        self.assertEqual(Booking.objects.count(), 1)

    def test_seat_page_prompts_sign_in_when_signed_out(self):
        """AC-8: signed out, the seats are visible but booking asks you to sign in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to book a seat")
        self.assertContains(response, f'{reverse("login")}?next={self.url}')
        self.assertNotContains(response, 'name="seat"')

    def test_anonymous_page_booking_redirects_to_login(self):
        """AC-8: a signed-out POST goes to sign-in, then back here, and books nothing."""
        response = self.client.post(self.url, {"seat": self.a1.pk})
        self.assertRedirects(
            response, f'{reverse("login")}?next={self.url}', fetch_redirect_response=False
        )
        self.assertFalse(Booking.objects.filter(seat=self.a1).exists())


class SameRulesEverywhereTests(APITestCase):
    """002 AC-6 — the page and /api/seats/ share one set of booking rules."""

    def setUp(self):
        self.dune = make_movie("Dune")
        self.a1 = seat(self.dune, "A1")
        self.page_url = reverse("book_seat", args=[self.dune.pk])
        self.api_url = reverse("seat-book", args=[self.a1.pk])

    def test_seat_booked_via_page_refused_via_seats_api(self):
        """AC-6: a seat booked on the page is 409 through the API."""
        self.client.force_login(make_user("sam"))
        self.client.post(self.page_url, {"seat": self.a1.pk})
        self.client.force_authenticate(make_user("alex"))
        response = self.client.post(self.api_url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_seat_booked_via_seats_api_refused_via_page(self):
        """AC-6: a seat booked through the API is refused on the page."""
        self.client.force_authenticate(make_user("sam"))
        self.assertEqual(self.client.post(self.api_url).status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(None)
        self.client.force_login(make_user("alex"))
        response = self.client.post(self.page_url, {"seat": self.a1.pk}, follow=True)
        self.assertContains(response, "Seat A1 for Dune is already booked.")
        self.assertEqual(Booking.objects.get(seat=self.a1).user.username, "sam")


class AdminTests(TestCase):
    """002 plan §6 — the admin site can't put a seat's status out of step."""

    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "pw-admin-123")
        self.client.force_login(self.admin)
        self.dune = make_movie("Dune")
        self.booking = services.book_seat(make_user("sam"), seat(self.dune, "A1"))

    def test_admin_pages_load(self):
        """Every model's list and change page renders for staff."""
        for name, obj in (("movie", self.dune), ("seat", self.booking.seat), ("booking", self.booking)):
            with self.subTest(model=name):
                changelist = reverse(f"admin:bookings_{name}_changelist")
                self.assertEqual(self.client.get(changelist).status_code, 200)
                change = reverse(f"admin:bookings_{name}_change", args=[obj.pk])
                self.assertEqual(self.client.get(change).status_code, 200)

    def test_admin_cannot_add_bookings_or_edit_seat_status(self):
        """Bookings are made only through book_seat; seat status is read-only."""
        response = self.client.get(reverse("admin:bookings_booking_add"))
        self.assertEqual(response.status_code, 403)
        change = self.client.get(reverse("admin:bookings_seat_change", args=[self.booking.seat.pk]))
        self.assertNotIn("booking_status", change.context["adminform"].form.fields)

    def test_movie_created_in_admin_gets_seats(self):
        """AC-13: a movie added through the admin site comes with 40 seats."""
        self.client.post(
            reverse("admin:bookings_movie_add"),
            {"title": "Up", "description": "", "release_date": "2009-05-29", "duration": 96},
        )
        self.assertEqual(Movie.objects.get(title="Up").seats.count(), 40)


# ---------------------------------------------------------------------------
# 003 — Booking history
# ---------------------------------------------------------------------------


class CancelBookingServiceTests(TestCase):
    """003 AC-9 — cancelling frees the seat."""

    def test_cancel_booking_frees_seat(self):
        """AC-9: the booking is deleted and the seat is available to anyone again."""
        dune = make_movie("Dune")
        a1 = seat(dune, "A1")
        booking = services.book_seat(make_user("sam"), a1)
        services.cancel_booking(booking)
        self.assertFalse(Booking.objects.exists())
        a1.refresh_from_db()
        self.assertFalse(a1.is_booked)
        services.book_seat(make_user("alex"), a1)  # free again


class BookingApiTests(APITestCase):
    """003 — /api/bookings/ (AC-2, AC-3, AC-6 to AC-10)."""

    def setUp(self):
        self.dune = make_movie("Dune")
        self.up = make_movie("Up", date(2009, 5, 29), 96)
        self.sam = make_user("sam")
        self.alex = make_user("alex")
        self.sam_booking = services.book_seat(self.sam, seat(self.dune, "A1"))
        self.alex_booking = services.book_seat(self.alex, seat(self.dune, "A2"))
        self.client.force_authenticate(self.sam)
        self.list_url = reverse("booking-list")

    def detail_url(self, booking):
        return reverse("booking-detail", args=[booking.pk])

    def test_list_bookings_only_returns_own(self):
        """AC-2: Sam's list has Sam's booking and none of Alex's."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([b["id"] for b in response.data], [self.sam_booking.pk])
        self.assertEqual(response.data[0]["user"], "sam")

    def test_cannot_retrieve_another_users_booking(self):
        """AC-3: someone else's booking is 404, the same as a missing one."""
        response = self.client.get(self.detail_url(self.alex_booking))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotIn("seat", response.data)
        self.assertEqual(
            self.client.get(reverse("booking-detail", args=[9999])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        response = self.client.get(self.detail_url(self.sam_booking))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["seat_number"], "A1")

    def test_bookings_newest_first(self):
        """AC-8: the newest booking comes first."""
        newer = services.book_seat(self.sam, seat(self.up, "B2"))
        ids = [b["id"] for b in self.client.get(self.list_url).data]
        self.assertEqual(ids, [newer.pk, self.sam_booking.pk])

    def test_bookings_api_requires_sign_in(self):
        """AC-6: signed out, list, create, retrieve and delete are all 401."""
        self.client.force_authenticate(None)
        free_seat = seat(self.dune, "A3")
        attempts = [
            self.client.get(self.list_url),
            self.client.post(self.list_url, {"seat": free_seat.pk}, format="json"),
            self.client.get(self.detail_url(self.sam_booking)),
            self.client.delete(self.detail_url(self.sam_booking)),
        ]
        for response in attempts:
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Booking.objects.count(), 2)

    def test_create_booking_via_bookings_api(self):
        """AC-7: POST {"seat": id} is 201 with the booking, and the seat is booked."""
        b2 = seat(self.up, "B2")
        response = self.client.post(self.list_url, {"seat": b2.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["movie"], self.up.pk)
        self.assertEqual(response.data["seat_number"], "B2")
        self.assertEqual(response.data["user"], "sam")
        b2.refresh_from_db()
        self.assertTrue(b2.is_booked)

    def test_create_booking_ignores_user_in_request_data(self):
        """AC-7 / 002 AC-5: "user" (and "movie") in the request are ignored."""
        b2 = seat(self.up, "B2")
        response = self.client.post(
            self.list_url,
            {"seat": b2.pk, "user": self.alex.pk, "movie": self.dune.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(seat=b2)
        self.assertEqual(booking.user, self.sam)
        self.assertEqual(booking.movie, self.up)

    def test_seat_booked_via_seats_api_refused_via_bookings_api(self):
        """AC-7 / 002 AC-6: a seat booked through /api/seats/ is 409 here."""
        a3 = seat(self.dune, "A3")
        self.client.post(reverse("seat-book", args=[a3.pk]))
        self.client.force_authenticate(self.alex)
        response = self.client.post(self.list_url, {"seat": a3.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["detail"], "Seat A3 for Dune is already booked.")
        self.assertEqual(Booking.objects.get(seat=a3).user, self.sam)

    def test_create_booking_bad_seat_400(self):
        """AC-7: a missing or nonexistent seat is 400 with an error for seat."""
        for data in ({}, {"seat": 9999}):
            with self.subTest(data=data):
                response = self.client.post(self.list_url, data, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("seat", response.data)

    def test_cancel_booking_via_api(self):
        """AC-9: DELETE is 204 and frees the seat."""
        response = self.client.delete(self.detail_url(self.sam_booking))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Booking.objects.filter(pk=self.sam_booking.pk).exists())
        self.assertFalse(seat(self.dune, "A1").is_booked)

    def test_cannot_cancel_another_users_booking(self):
        """AC-9: deleting Alex's booking is 404 and leaves it alone."""
        response = self.client.delete(self.detail_url(self.alex_booking))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Booking.objects.filter(pk=self.alex_booking.pk).exists())
        self.assertTrue(seat(self.dune, "A2").is_booked)

    def test_bookings_cannot_be_edited(self):
        """AC-10: PUT and PATCH are 405 and change nothing."""
        b2 = seat(self.up, "B2")
        for method in (self.client.put, self.client.patch):
            with self.subTest(method=method.__name__):
                response = method(self.detail_url(self.sam_booking), {"seat": b2.pk}, format="json")
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.sam_booking.refresh_from_db()
        self.assertEqual(self.sam_booking.seat.seat_number, "A1")


class BookingHistoryPageTests(TestCase):
    """003 — My Bookings page (AC-1, AC-2, AC-4 to AC-6, AC-8, AC-9)."""

    def setUp(self):
        self.dune = make_movie("Dune")
        self.up = make_movie("Up", date(2009, 5, 29), 96)
        self.sam = make_user("sam")
        self.alex = make_user("alex")
        self.url = reverse("booking_history")

    def test_booking_history_shows_movie_seat_and_date(self):
        """AC-1: each booking shows its movie, seat and booking date."""
        booking = services.book_seat(self.sam, seat(self.dune, "A1"))
        self.client.force_login(self.sam)
        response = self.client.get(self.url)
        self.assertContains(response, "Dune")
        self.assertContains(response, "A1")
        local_date = timezone.localtime(booking.booking_date)
        self.assertContains(response, format_date(local_date, "F j, Y"))

    def test_booking_history_page_only_shows_own(self):
        """AC-2: Alex's bookings never appear on Sam's page."""
        services.book_seat(self.sam, seat(self.dune, "A1"))
        services.book_seat(self.alex, seat(self.up, "C7"))
        self.client.force_login(self.sam)
        response = self.client.get(self.url)
        self.assertEqual([b.user for b in response.context["bookings"]], [self.sam])
        self.assertNotContains(response, "C7")

    def test_bookings_newest_first_on_page(self):
        """AC-8: the newest booking is listed first."""
        services.book_seat(self.sam, seat(self.dune, "A1"))
        services.book_seat(self.sam, seat(self.up, "B2"))
        self.client.force_login(self.sam)
        titles = [b.movie.title for b in self.client.get(self.url).context["bookings"]]
        self.assertEqual(titles, ["Up", "Dune"])

    def test_booking_history_uses_base_template(self):
        """AC-4: the page extends base.html."""
        self.client.force_login(self.sam)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "bookings/booking_history.html")
        self.assertTemplateUsed(response, "bookings/base.html")

    def test_navbar_links_to_movies_and_my_bookings(self):
        """AC-4: the navbar links to Movies and My Bookings."""
        self.client.force_login(self.sam)
        response = self.client.get(reverse("movie_list"))
        self.assertContains(response, f'href="{reverse("movie_list")}"')
        self.assertContains(response, f'href="{self.url}"')
        self.assertContains(response, "My Bookings")

    def test_booking_history_empty_state(self):
        """AC-5: no bookings shows a message and a link to the movies."""
        self.client.force_login(self.sam)
        response = self.client.get(self.url)
        self.assertContains(response, "You have no bookings yet.")
        self.assertContains(response, f'href="{reverse("movie_list")}"')

    def test_booking_history_requires_sign_in(self):
        """AC-6: signed out, the page sends you to sign in and then back."""
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f'{reverse("login")}?next={self.url}', fetch_redirect_response=False
        )

    def test_cancel_booking_via_page(self):
        """AC-9: Cancel removes the booking, frees the seat and confirms."""
        booking = services.book_seat(self.sam, seat(self.dune, "A1"))
        self.client.force_login(self.sam)
        cancel_url = reverse("cancel_booking", args=[booking.pk])
        self.assertContains(self.client.get(self.url), f'action="{cancel_url}"')
        response = self.client.post(cancel_url, follow=True)
        self.assertRedirects(response, self.url)
        self.assertContains(response, "Cancelled your booking of seat A1 for Dune.")
        self.assertContains(response, "You have no bookings yet.")
        self.assertFalse(seat(self.dune, "A1").is_booked)

    def test_cannot_cancel_another_users_booking_via_page(self):
        """AC-9: cancelling Alex's booking is 404 and leaves it alone."""
        booking = services.book_seat(self.alex, seat(self.dune, "A1"))
        self.client.force_login(self.sam)
        response = self.client.post(reverse("cancel_booking", args=[booking.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Booking.objects.filter(pk=booking.pk).exists())

    def test_cancel_needs_post_and_sign_in(self):
        """AC-9 / plan §6: a GET can't cancel, and signed-out users go to sign in."""
        booking = services.book_seat(self.sam, seat(self.dune, "A1"))
        cancel_url = reverse("cancel_booking", args=[booking.pk])
        response = self.client.post(cancel_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
        self.client.force_login(self.sam)
        self.assertEqual(self.client.get(cancel_url).status_code, 405)
        self.assertTrue(Booking.objects.filter(pk=booking.pk).exists())


class AdminDeleteBookingTests(TestCase):
    """003 T8 / 002 plan §6 — admin deletes go through cancel_booking."""

    def setUp(self):
        admin_user = User.objects.create_superuser("admin", "admin@example.com", "pw-admin-123")
        self.client.force_login(admin_user)
        self.dune = make_movie("Dune")

    def test_admin_delete_frees_seat(self):
        """Deleting one booking in the admin site frees its seat."""
        booking = services.book_seat(make_user("sam"), seat(self.dune, "A1"))
        url = reverse("admin:bookings_booking_delete", args=[booking.pk])
        self.client.post(url, {"post": "yes"})
        self.assertFalse(Booking.objects.exists())
        self.assertFalse(seat(self.dune, "A1").is_booked)

    def test_admin_bulk_delete_frees_seats(self):
        """The "delete selected" action frees every seat too."""
        sam = make_user("sam")
        bookings = [services.book_seat(sam, seat(self.dune, n)) for n in ("A1", "A2")]
        self.client.post(
            reverse("admin:bookings_booking_changelist"),
            {"action": "delete_selected", "_selected_action": [b.pk for b in bookings], "post": "yes"},
        )
        self.assertFalse(Booking.objects.exists())
        self.assertFalse(self.dune.seats.filter(booking_status="booked").exists())
