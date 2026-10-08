"""API viewsets and HTML page views for the bookings app."""

from rest_framework import viewsets

from .models import Movie
from .serializers import MovieSerializer


class MovieViewSet(viewsets.ModelViewSet):
    """CRUD for movies at /api/movies/ (001). Anyone reads; signed-in users write."""

    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
