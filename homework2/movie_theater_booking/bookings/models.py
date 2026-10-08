"""Data models for the movie theater: movies, their seats, and bookings."""

from django.core.validators import MinValueValidator
from django.db import models


class Movie(models.Model):
    """A movie the theater is showing (spec 001)."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    release_date = models.DateField()
    # PositiveIntegerField still allows 0, and a zero-minute movie is not valid.
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], help_text="Length in whole minutes."
    )

    class Meta:
        ordering = ["-release_date"]

    def __str__(self):
        return self.title

    @property
    def duration_display(self):
        """Duration as hours and minutes, e.g. 155 -> "2h 35m" (001 AC-3)."""
        hours, minutes = divmod(self.duration, 60)
        parts = [f"{hours}h"] if hours else []
        if minutes or not hours:
            parts.append(f"{minutes}m")
        return " ".join(parts)
