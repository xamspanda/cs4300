# Tasks: Booking history

**Plan:** [plan.md](plan.md)

> Each task is one small test-first increment and one commit: red → green → refactor when the behavior is missing,
> or a verification test if it already passes. Do them in order.
> Each task names its test and the acceptance criterion (AC-#) it covers.
> The AI assistant ticks the box when the task's tests pass. **You** commit.

- [ ] **T1** — `cancel_booking()` service · test: `test_cancel_booking_frees_seat` · covers: AC-9
- [ ] **T2** — `BookingViewSet` list + retrieve, own bookings only, newest first · tests: `test_list_bookings_only_returns_own`, `test_cannot_retrieve_another_users_booking`, `test_bookings_newest_first` · covers: AC-2, AC-3, AC-8
- [ ] **T3** — Sign-in required for the API · test: `test_bookings_api_requires_sign_in` · covers: AC-6
- [ ] **T4** — `POST /api/bookings/` through `book_seat()` · tests: `test_create_booking_via_bookings_api`, `test_create_booking_ignores_user_in_request_data`, `test_seat_booked_via_seats_api_refused_via_bookings_api`, `test_create_booking_bad_seat_400` · covers: AC-7
- [ ] **T5** — `DELETE /api/bookings/<id>/` through `cancel_booking()`; no `PUT`/`PATCH` · tests: `test_cancel_booking_via_api`, `test_cannot_cancel_another_users_booking`, `test_bookings_cannot_be_edited` · covers: AC-9, AC-10
- [ ] **T6** — My Bookings page + navbar link · tests: `test_booking_history_shows_movie_seat_and_date`, `test_booking_history_page_only_shows_own`, `test_booking_history_uses_base_template`, `test_navbar_links_to_movies_and_my_bookings`, `test_booking_history_empty_state`, `test_booking_history_requires_sign_in` · covers: AC-1, AC-2, AC-4, AC-5, AC-6
- [ ] **T7** — Cancel from the page · tests: `test_cancel_booking_via_page`, `test_cannot_cancel_another_users_booking_via_page` · covers: AC-9
- [ ] **T8** — Admin deletes bookings through `cancel_booking()` · test: `test_admin_delete_frees_seat` · covers: 002 plan §6
- [ ] **T9** — Behave: "See my bookings", "No bookings yet", "Cancel a booking" · covers: AC-1, AC-5, AC-9

## Done when
- [ ] Every acceptance criterion in `spec.md` has a passing test
- [ ] Full suite green: `python manage.py test`
- [ ] `python manage.py behave` passes
- [ ] Coverage ≥ 80%
- [ ] `AI-USAGE.md` updated
