"""URL routes for the bookings app: the REST API under api/ and the HTML pages."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("movies", views.MovieViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
]
