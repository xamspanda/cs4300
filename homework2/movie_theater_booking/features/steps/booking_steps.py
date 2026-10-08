"""Behave steps for seat booking (002) and booking history (003)."""

from behave import given, then, when
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.dateformat import format as format_date

from bookings import services
from bookings.models import Booking, Movie, Seat

User = get_user_model()


def get_user(username):
    user, _ = User.objects.get_or_create(username=username)
    return user


def get_seat(movie_title, seat_number):
    return Seat.objects.get(movie__title=movie_title, seat_number=seat_number)


@given('seat "{number}" for "{title}" is booked by "{username}"')
def step_seat_booked_by(context, number, title, username):
    services.book_seat(get_user(username), get_seat(title, number))


@given('I am signed in as "{username}"')
def step_signed_in(context, username):
    context.test.client.force_login(get_user(username))


@given("I am not signed in")
def step_not_signed_in(context):
    context.test.client.logout()


@when('I click "Book Now" for "{title}"')
def step_click_book_now(context, title):
    movie = Movie.objects.get(title=title)
    link = reverse("book_seat", args=[movie.pk])
    listing = context.test.client.get(reverse("movie_list"))
    context.test.assertContains(listing, f'href="{link}"')
    context.movie = movie
    context.response = context.test.client.get(link)


@when('I open the seat booking page for "{title}"')
def step_open_seat_page(context, title):
    context.movie = Movie.objects.get(title=title)
    context.response = context.test.client.get(reverse("book_seat", args=[context.movie.pk]))


@when('I book seat "{number}"')
def step_book_seat(context, number):
    seat = context.movie.seats.get(seat_number=number)
    context.response = context.test.client.post(
        reverse("book_seat", args=[context.movie.pk]), {"seat": seat.pk}, follow=True
    )


@then('I see seat "{number}" as {state}')
def step_see_seat_state(context, number, state):
    context.test.assertContains(context.response, f'aria-label="Seat {number}, {state}"')


@then('seat "{number}" for "{title}" is booked by "{username}"')
def step_seat_is_booked_by(context, number, title, username):
    seat = get_seat(title, number)
    context.test.assertTrue(seat.is_booked)
    context.test.assertEqual(Booking.objects.get(seat=seat).user.username, username)


@then('seat "{number}" for "{title}" is not booked')
def step_seat_not_booked(context, number, title):
    seat = get_seat(title, number)
    context.test.assertFalse(seat.is_booked)
    context.test.assertFalse(Booking.objects.filter(seat=seat).exists())


@then("I am sent to the sign-in page")
def step_sent_to_sign_in(context):
    context.test.assertEqual(context.response.resolver_match.url_name, "login")


@when("I open My Bookings")
def step_open_my_bookings(context):
    context.response = context.test.client.get(reverse("booking_history"))


@when('I cancel my booking of seat "{number}" for "{title}"')
def step_cancel_booking(context, number, title):
    booking = Booking.objects.get(seat=get_seat(title, number))
    cancel_url = reverse("cancel_booking", args=[booking.pk])
    # The Cancel button on the page must point at this booking.
    context.test.assertContains(context.response, f'action="{cancel_url}"')
    context.response = context.test.client.post(cancel_url, follow=True)


@then("I see today's date")
def step_see_today(context):
    today = timezone.localdate()
    context.test.assertContains(context.response, format_date(today, "F j, Y"))
