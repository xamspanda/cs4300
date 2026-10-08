# Tasks: Seat booking

**Plan:** [plan.md](plan.md)

> Each task is one small test-first increment and one commit: red → green → refactor when the behavior is missing,
> or a verification test if it already passes. Do them in order.
> Each task names its test and the acceptance criterion (AC-#) it covers.
> The AI assistant ticks the box when the task's tests pass. **You** commit.

- [x] **T1** — `Seat` model (movie, seat_number, booking_status) + migration · test: `test_seat_str_and_default_status` · covers: Data
- [x] **T2** — `create_seats_for_movie` + `post_save` signal · test: `test_new_movie_gets_40_available_seats` · covers: AC-13
- [x] **T3** — `Booking` model + unique constraint on seat + migration · test: `test_duplicate_booking_rejected_by_database` · covers: AC-4
- [x] **T4** — `book_seat()` service: saves booking, sets status · test: `test_book_seat_creates_booking_and_marks_seat_booked` · covers: AC-2
- [x] **T5** — `book_seat()` refuses a taken seat, including a duplicate saved behind its back · tests: `test_book_seat_refuses_taken_seat`, `test_book_seat_turns_integrity_error_into_seat_unavailable` · covers: AC-3, AC-4
- [x] **T6** — `SeatSerializer` + `SeatViewSet` (read-only) + route; filters · tests: `test_list_seats_filtered_by_movie`, `test_list_seats_filtered_by_status`, `test_list_seats_bad_movie_param_400` · covers: AC-10
- [x] **T7** — Seats can't be changed via API · test: `test_seats_cannot_be_changed_via_api` · covers: AC-12
- [x] **T8** — `BookingSerializer` + `SeatViewSet.book` → 201 · tests: `test_book_seat_via_seats_api`, `test_booking_user_is_request_user_not_request_data` · covers: AC-11, AC-5
- [x] **T9** — `book` errors: taken → 409, missing → 404, anonymous → 401 · tests: `test_book_taken_seat_via_api_409`, `test_duplicate_booking_returns_error_not_500`, `test_book_missing_seat_api_404`, `test_anonymous_api_booking_401` · covers: AC-3, AC-4, AC-8, AC-9
- [x] **T10** — Sign up / sign in / sign out pages · tests: `test_signup_signs_in_and_redirects`, `test_signup_rejects_taken_username_and_mismatch`, `test_sign_out_and_in_again` · covers: AC-14
- [x] **T11** — `seat_booking` page (GET) + "Book Now" link · tests: `test_seat_page_shows_booked_and_available_seats`, `test_movie_list_book_now_links_to_seat_page`, `test_seat_booking_uses_base_template`, `test_seat_page_missing_movie_404` · covers: AC-1, AC-7, AC-9
- [x] **T12** — Book through the page (POST) · tests: `test_book_seat_via_page`, `test_page_booking_user_is_request_user`, `test_book_taken_seat_via_page_shows_error`, `test_book_other_movies_seat_via_page_refused` · covers: AC-2, AC-3, AC-5, AC-9
- [x] **T13** — Signed-out page: sign-in prompt; POST redirects to login · tests: `test_seat_page_prompts_sign_in_when_signed_out`, `test_anonymous_page_booking_redirects_to_login` · covers: AC-8
- [x] **T14** — Same rules everywhere · tests: `test_seat_booked_via_page_refused_via_seats_api`, `test_seat_booked_via_seats_api_refused_via_page` · covers: AC-6
- [ ] **T15** — Admin: Movie, Seat (status read-only), Booking (no add) · covers: plan §6
- [ ] **T16** — Behave: "See which seats are free", "Book an available seat", "Seat already taken", "Must sign in to book" · covers: AC-1, AC-2, AC-3, AC-8

## Done when
- [ ] Every acceptance criterion in `spec.md` has a passing test
- [ ] Full suite green: `python manage.py test`
- [ ] `python manage.py behave` passes
- [ ] Coverage ≥ 80%
- [ ] `AI-USAGE.md` updated
