"""Project URL routes: the admin site plus everything in the bookings app."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("bookings.urls")),
]
