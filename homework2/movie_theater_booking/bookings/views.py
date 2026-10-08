"""API viewsets and HTML page views for the bookings app."""

from django.shortcuts import render
from rest_framework import viewsets

from .models import Movie
from .serializers import MovieSerializer


class MovieViewSet(viewsets.ModelViewSet):
    """CRUD for movies at /api/movies/ (001). Anyone reads; signed-in users write."""

    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


def movie_list(request):
    """The home page: every movie with a Book Now button (001 AC-1 to AC-3)."""
    return render(request, "bookings/movie_list.html", {"movies": Movie.objects.all()})
