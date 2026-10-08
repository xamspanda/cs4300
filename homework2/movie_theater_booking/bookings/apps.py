from django.apps import AppConfig


class BookingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bookings"

    def ready(self):
        # Importing the module connects its signal handlers.
        from . import signals  # noqa: F401
