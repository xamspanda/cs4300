"""URL routes for the bookings app: the REST API under api/ and the HTML pages."""

from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("movies", views.MovieViewSet)
router.register("seats", views.SeatViewSet, basename="seat")
router.register("bookings", views.BookingViewSet, basename="booking")

urlpatterns = [
    path("", views.movie_list, name="movie_list"),
    path("movies/<int:movie_id>/book/", views.seat_booking, name="book_seat"),
    path("bookings/", views.booking_history, name="booking_history"),
    path("bookings/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("accounts/signup/", views.signup, name="signup"),
    # Only sign in and sign out; password reset and change are out of scope (002 §6).
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/", include(router.urls)),
]
