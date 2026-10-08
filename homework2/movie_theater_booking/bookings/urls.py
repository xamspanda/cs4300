"""URL routes for the bookings app: the REST API under api/ and the HTML pages."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("movies", views.MovieViewSet)
router.register("seats", views.SeatViewSet, basename="seat")

urlpatterns = [
    path("", views.movie_list, name="movie_list"),
    path("api/", include(router.urls)),
]
