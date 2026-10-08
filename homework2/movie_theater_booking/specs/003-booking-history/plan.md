# Plan: Booking history

**Spec:** [spec.md](spec.md)   **Status:** Approved

## 1. Approach
No new models. `BookingViewSet` is built from DRF mixins (list, retrieve, create, destroy) rather
than a full `ModelViewSet`, so `PUT`/`PATCH` simply don't exist and return 405 (AC-10). It requires
`IsAuthenticated`, and `get_queryset()` returns only `request.user`'s bookings, so list, retrieve and
destroy all hide other users' bookings behind a 404 (AC-2, AC-3, AC-9). `create` validates the seat
with `BookingSerializer` and then calls 002's `book_seat()`; `perform_destroy` calls
`cancel_booking()`, added next to it in `services.py`. The My Bookings page is a `login_required`
function view over the same filtered query, and its Cancel button posts to a small `cancel_booking`
view that also calls the service.

**Rejected:** a `ModelViewSet` with `update` overridden to return 405. It would work, but it lists
operations the resource doesn't support and relies on remembering to block them.

## 2. Data model
| Model | Field | Type | Constraints | Spec ref |
|---|---|---|---|---|
| Booking | — | `Meta.ordering = ["-booking_date", "-id"]` (id breaks ties within the same instant) | — | AC-8 |

## 3. Endpoints / views
| Method | URL | View / ViewSet | Returns | Spec ref |
|---|---|---|---|---|
| GET | `/api/bookings/` | BookingViewSet.list: `get_queryset()` returns only `request.user`'s bookings | 200 list / 401 | AC-2, AC-6, AC-8 |
| GET | `/api/bookings/<id>/` | BookingViewSet.retrieve: same filtered queryset | 200 / 404 / 401 | AC-3 |
| POST | `/api/bookings/` | BookingViewSet.create: calls 002's booking operation, with `user=request.user` | 201 / 400 / 409 / 401 | AC-6, AC-7 |
| DELETE | `/api/bookings/<id>/` | BookingViewSet.destroy → `cancel_booking()` | 204 / 404 / 401 | AC-9 |
| PUT/PATCH | `/api/bookings/<id>/` | not provided | 405 | AC-10 |
| GET | `/bookings/` (named `booking_history`) | `booking_history` view (`login_required`) → `booking_history.html` | HTML / redirect to login | AC-1, AC-2, AC-4, AC-5, AC-6, AC-8 |
| POST | `/bookings/<id>/cancel/` (named `cancel_booking`) | `cancel_booking` view (`login_required`, `require_POST`) | 302 + message / 404 | AC-9 |

## 4. Files to create / change
| File | Change |
|---|---|
| `bookings/models.py` | `Booking.Meta.ordering` (a small `AlterModelOptions` migration; the table is unchanged) |
| `bookings/services.py` | `cancel_booking(booking)`: delete it and set the seat `available` in one transaction |
| `bookings/views.py` | `BookingViewSet`, `booking_history`, `cancel_booking` |
| `bookings/urls.py` | register `bookings` on the router; page routes |
| `bookings/admin.py` | deleting bookings in the admin site goes through `cancel_booking` |
| `bookings/templates/bookings/base.html` | Add the My Bookings link to the navbar, now that its route exists |
| `bookings/templates/bookings/booking_history.html` | table of bookings, Cancel buttons, empty state |
| `bookings/tests.py`, `features/booking_history.feature`, `features/steps/` | tests below |

## 5. Test strategy
| Spec ref | Test type (unit / integration / Behave) | Test name / scenario |
|---|---|---|
| AC-1 | view test + Behave | `test_booking_history_shows_movie_seat_and_date`; "See my bookings" |
| AC-2 | API + view test | `test_list_bookings_only_returns_own`, `test_booking_history_page_only_shows_own` |
| AC-3 | API | `test_cannot_retrieve_another_users_booking` |
| AC-4 | view test | `test_booking_history_uses_base_template` (`assertTemplateUsed`), `test_navbar_links_to_movies_and_my_bookings` |
| AC-5 | view test + Behave | `test_booking_history_empty_state`; "No bookings yet" |
| AC-6 | view + API | `test_booking_history_requires_sign_in`, `test_bookings_api_requires_sign_in` |
| AC-7 | API | `test_create_booking_via_bookings_api`, `test_create_booking_ignores_user_in_request_data`, `test_seat_booked_via_seats_api_refused_via_bookings_api`, `test_create_booking_bad_seat_400` |
| AC-8 | API + view test | `test_bookings_newest_first` |
| AC-9 | unit + API + view + Behave | `test_cancel_booking_frees_seat`, `test_cancel_booking_via_api`, `test_cannot_cancel_another_users_booking`, `test_cancel_booking_via_page`; "Cancel a booking" |
| AC-10 | API | `test_bookings_cannot_be_edited` |

## 6. Risks & decisions
- Filter in `get_queryset()`, not only in the template or the list view. Otherwise
  `/api/bookings/<id>/` (and delete) would still expose other users' bookings.
- The Cancel button is a POST form (with a browser confirm prompt), never a GET link, so following a
  link or a prefetch can't cancel a booking, and Django's CSRF protection applies.
- `BookingSerializer` is shared with 002's `SeatViewSet.book`. `seat` is writable (and validated as
  an existing seat, giving 400), while `movie`, `user` and `booking_date` are read-only.
