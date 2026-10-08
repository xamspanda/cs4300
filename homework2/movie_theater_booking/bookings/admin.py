"""Admin site setup. Bookings are made only through services.book_seat, so the
admin site can view them but not add them, a seat's status is read-only, and
deleting a booking here cancels it through services.cancel_booking."""

from django.contrib import admin

from . import services
from .models import Booking, Movie, Seat


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "release_date", "duration"]
    search_fields = ["title"]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ["seat_number", "movie", "booking_status"]
    list_filter = ["booking_status", "movie"]
    readonly_fields = ["booking_status"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["user", "movie", "seat", "booking_date"]
    list_filter = ["movie"]
    readonly_fields = ["movie", "seat", "user", "booking_date"]

    def has_add_permission(self, request):
        return False

    def delete_model(self, request, obj):
        services.cancel_booking(obj)

    def delete_queryset(self, request, queryset):
        for booking in queryset:
            services.cancel_booking(booking)
