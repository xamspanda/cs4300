"""Serializers that turn the bookings models into JSON for the REST API."""

from rest_framework import serializers

from .models import Movie


class MovieSerializer(serializers.ModelSerializer):
    """A movie; the model's validators reject a duration of 0 or less (001 AC-6)."""

    class Meta:
        model = Movie
        fields = ["id", "title", "description", "release_date", "duration"]
