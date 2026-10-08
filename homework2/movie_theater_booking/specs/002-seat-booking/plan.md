# Plan: Seat booking

**Spec:** [spec.md](spec.md)   **Status:** Approved

## 1. Approach
`Seat` gets a `movie` foreign key, and `Booking` links movie, seat and user. A database unique
constraint on `Booking.seat` is what guarantees no double booking (AC-4).

- **One booking operation.** `bookings/services.py` holds `book_seat(user, seat)` (and
  `cancel_booking(booking)` in 003). The seat booking page, `SeatViewSet.book` and
  `BookingViewSet.create` (003) all call it (AC-6). It lives in its own module, not in a model or a
  serializer, because it changes two models in one transaction, and a serializer can't be called
  by the HTML page. It raises `SeatUnavailable`. The page turns that into a message, and the API
  into **409**.
- **Seats come with their movie.** A `post_save` signal on `Movie` calls
  `create_seats_for_movie(movie)` when a movie is created, so the API, the admin site and the seed
  command all get seats (AC-13) without each remembering to do it.
- **Sign-in** uses Django's built-in `django.contrib.auth.urls` (login and logout) plus one small
  `signup` view built on `UserCreationForm` (AC-14).

**Rejected:** putting the booking rules in `BookingSerializer.create()`. The API would follow them,
but the HTML page would need its own copy, which breaks AC-6 the first time one copy changes.
**Rejected:** a separate "Screening" model between Movie and Seat. It's closer to a real theater,
but the assignment's models have no showtimes, and a movie *is* its one screening here.

## 2. Data model
| Model | Field | Type | Constraints | Spec ref |
|---|---|---|---|---|
| Seat | movie | ForeignKey(Movie, `on_delete=CASCADE`, `related_name="seats"`) | required | AC-1, AC-10, AC-13 |
| Seat | seat_number | CharField(max_length=3) | e.g. `A1`; `UniqueConstraint(movie, seat_number)` | Data, AC-13 |
| Seat | booking_status | CharField with `TextChoices` `available` / `booked` | default `available`; written only by `services` | AC-2, AC-10, AC-11 |
| Seat | — | `Meta.ordering = ["movie", "seat_number"]`; `__str__` → `"A1 – Dune"` | — | AC-1 |
| Booking | movie | ForeignKey(Movie, CASCADE) | always `seat.movie` (set by `book_seat`) | Data |
| Booking | seat | ForeignKey(Seat, CASCADE, `related_name="bookings"`) | `UniqueConstraint(fields=["seat"], name="one_booking_per_seat")` | AC-4 |
| Booking | user | ForeignKey to the user model | set from `request.user` on the server; read-only in the serializer | AC-5 |
| Booking | booking_date | DateTimeField(`auto_now_add=True`) | set when booked | AC-2 |

## 3. Endpoints / views
| Method | URL | View / ViewSet | Returns | Spec ref |
|---|---|---|---|---|
| GET | `/movies/<movie_id>/book/` (named `book_seat`) | `seat_booking` view → `seat_booking.html` | HTML / 404 | AC-1, AC-7, AC-8, AC-9 |
| POST | `/movies/<movie_id>/book/` (`seat` in form) | `seat_booking` view → `book_seat()` → redirect back | 302 + message / redirect to login | AC-2, AC-3, AC-5, AC-8, AC-9 |
| GET | `/api/seats/` (`?movie=`, `?booking_status=`) | SeatViewSet.list | 200 / 400 | AC-10 |
| GET | `/api/seats/<id>/` | SeatViewSet.retrieve | 200 / 404 | AC-10 |
| POST | `/api/seats/<id>/book/` | SeatViewSet.book (`@action`, `IsAuthenticated`) → `book_seat()` | 201 / 401 / 404 / 409 | AC-3, AC-5, AC-6, AC-8, AC-9, AC-11 |
| POST/PUT/PATCH/DELETE | `/api/seats/…` | not provided (`ReadOnlyModelViewSet`) | 405 | AC-12 |
| GET/POST | `/accounts/login/`, POST `/accounts/logout/` | `django.contrib.auth.urls` | HTML | AC-14 |
| GET/POST | `/accounts/signup/` (named `signup`) | `signup` view (`UserCreationForm`) | HTML / 302 | AC-14 |

## 4. Files to create / change
| File | Change |
|---|---|
| `bookings/models.py` | `Seat`, `Booking` + migration |
| `bookings/services.py` | `SeatUnavailable`, `create_seats_for_movie`, `book_seat` |
| `bookings/signals.py`, `bookings/apps.py` | create seats when a movie is created; connect in `ready()` |
| `bookings/serializers.py` | `SeatSerializer`, `BookingSerializer` |
| `bookings/views.py` | `SeatViewSet` (+ `book` action), `seat_booking`, `signup` |
| `bookings/urls.py`, `movie_theater_booking/urls.py` | seats route, `book_seat`, `signup`; include `django.contrib.auth.urls` |
| `bookings/admin.py` | Movie, Seat (status read-only), Booking (no add) |
| `bookings/templates/bookings/movie_list.html` | Turn 001's disabled "Book Now" into `{% url 'book_seat' movie.id %}` |
| `bookings/templates/bookings/seat_booking.html` | seat grid by row; booked seats disabled; sign-in prompt when signed out |
| `bookings/templates/bookings/base.html` | messages, username + Sign out, or Sign in / Sign up |
| `bookings/templates/registration/login.html`, `signup.html` | Bootstrap forms |
| `bookings/tests.py`, `features/seat_booking.feature`, `features/steps/` | tests below |

## 5. Test strategy
| Spec ref | Test type (unit / integration / Behave) | Test name / scenario |
|---|---|---|
| AC-1 | view test + Behave | `test_seat_page_shows_booked_and_available_seats`, `test_movie_list_book_now_links_to_seat_page`; "See which seats are free" |
| AC-2 | view test + Behave | `test_book_seat_via_page`; "Book an available seat" |
| AC-3 | view + API | `test_book_taken_seat_via_page_shows_error`, `test_book_taken_seat_via_api_409`; Behave "Seat already taken" |
| AC-4 | unit | `test_duplicate_booking_rejected_by_database` (saving a second booking directly raises `IntegrityError`) |
| AC-4 | unit + API | `test_book_seat_turns_integrity_error_into_seat_unavailable`, `test_duplicate_booking_returns_error_not_500` |
| AC-5 | view + API | `test_page_booking_user_is_request_user`, `test_booking_user_is_request_user_not_request_data` |
| AC-6 | view + API | `test_seat_booked_via_page_refused_via_seats_api`, `test_seat_booked_via_seats_api_refused_via_page` |
| AC-7 | view test | `test_seat_booking_uses_base_template` (`assertTemplateUsed`) |
| AC-8 | view + API + Behave | `test_seat_page_prompts_sign_in_when_signed_out`, `test_anonymous_page_booking_redirects_to_login`, `test_anonymous_api_booking_401`; "Must sign in to book" |
| AC-9 | view + API | `test_seat_page_missing_movie_404`, `test_book_missing_seat_api_404`, `test_book_other_movies_seat_via_page_refused` |
| AC-10 | API | `test_list_seats_filtered_by_movie`, `test_list_seats_filtered_by_status`, `test_list_seats_bad_movie_param_400` |
| AC-11 | API | `test_book_seat_via_seats_api` |
| AC-12 | API | `test_seats_cannot_be_changed_via_api` |
| AC-13 | unit | `test_new_movie_gets_40_available_seats` |
| AC-14 | view test | `test_signup_signs_in_and_redirects`, `test_signup_rejects_taken_username_and_mismatch`, `test_sign_out_and_in_again` |

## 6. Risks & decisions
- **Double booking is a race.** A "seat already taken?" check before saving is race-prone: two
  requests can both pass it before either one saves. So `book_seat` doesn't pre-check at all. It
  locks the seat row (`select_for_update`, which PostgreSQL honours and SQLite ignores), then
  saves the booking inside a savepoint (`transaction.atomic()`). The unique constraint refuses a
  duplicate, and the `IntegrityError` becomes `SeatUnavailable`, the same answer as AC-3, never a 500.
  📖 **Book:** [§7.2.1 The Shared-Data Pattern](https://www.swebook.org/chapters/07-architectural-patterns/index.html#721-the-shared-data-pattern)
- **Never trust the client for `user`.** It is set from `request.user` (AC-5). A `user` value in
  the request data is **ignored**: the field is read-only, so the client still gets 201 and the
  booking shows their own username.
- **Keeping status and bookings consistent.** The booking row is the truth; `booking_status` is a
  copy that only `services.py` writes, in the same transaction as the booking change. The admin
  site shows it read-only, can't add bookings, and deletes bookings through `cancel_booking` (003).
  Seats can't be changed through the API (AC-12).
- **SQLite on Render** is wiped on each deploy. Acceptable for a homework demo: the build re-runs
  migrations and the seed command. Noted in the README.
