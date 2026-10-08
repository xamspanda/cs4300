"""Shared Behave steps. behave-django gives each scenario a fresh test database
and a Django TestCase in context.test, whose test client we drive here."""

from datetime import date

from behave import given, then, when
from django.urls import reverse

from bookings.models import Movie


def page_text(context):
    return context.response.content.decode()


@given('the movie "{title}" exists with description "{description}"')
def step_movie_with_description(context, title, description):
    Movie.objects.create(
        title=title, description=description, release_date=date(2021, 10, 22), duration=120
    )


@given('the movie "{title}" exists')
def step_movie_exists(context, title):
    Movie.objects.create(title=title, release_date=date(2021, 10, 22), duration=120)


@given("no movies exist")
def step_no_movies(context):
    Movie.objects.all().delete()


@when("I open the movie list page")
def step_open_movie_list(context):
    context.response = context.test.client.get(reverse("movie_list"))


@then('I see "{text}"')
def step_see_text(context, text):
    context.test.assertContains(context.response, text)


@then('I do not see "{text}"')
def step_do_not_see_text(context, text):
    context.test.assertNotContains(context.response, text)


@then('I see {count:d} "{label}" buttons')
def step_see_buttons(context, count, label):
    context.test.assertEqual(page_text(context).count(label), count)
