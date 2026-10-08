# Spec: Booking history

**Status:** Reviewed
**Author:** Laura  **Date:** 2026-10-08

## 1. Problem
Moviegoers need to see what they've booked. (Homework 2, or HW2, §1 "Check their booking history via the API";
§3.3 `BookingViewSet` "for users to book seats and view their booking history"; §3.5
`/api/bookings/`; template `booking_history.html`.)

## 2. User stories
- **US-1:** As a moviegoer, I want to see a list of my bookings, so that I know what I've reserved.
- **US-2:** As an API client, I want to view booking history and create bookings through `/api/bookings/`.
- **US-3:** As a moviegoer, I want my bookings kept private, so that other users can't see them.
- **US-4:** As a moviegoer, I want to cancel a booking, so that the seat is free for someone else
  when my plans change.

## 3. Acceptance criteria

**AC-1 (US-1): See my bookings**
- Given I am signed in and have booked seat A1 for "Dune"
- When I open My Bookings
- Then I see Dune, seat A1 and the booking date

**AC-2 (US-1, US-3): Only my bookings**
- Given users Sam and Alex each have bookings
- When Sam opens My Bookings, or sends `GET /api/bookings/`
- Then only Sam's bookings appear, and none of Alex's

**AC-3 (US-3): Someone else's booking**
- Given Alex has a booking with id 7
- When Sam sends `GET /api/bookings/7/`
- Then none of Alex's booking data is returned: the response is **404**, the same as for a booking
  that doesn't exist. (403 would confirm that booking 7 exists, which is itself information about
  another user. To Sam, Alex's bookings simply aren't there.)

**AC-4 (UI): Consistent layout**
- Given the My Bookings page
- When it renders
- Then it extends `base.html`, and the navbar now links to both Movies and My Bookings

**AC-5 (US-1): Empty state**
- Given I am signed in and have no bookings
- When I open My Bookings
- Then I see "You have no bookings yet." and a link to the movie list

**AC-6 (US-1, US-2, US-3): Not signed in**
- Given I am not signed in
- When I open My Bookings
- Then I am sent to the sign-in page, and back to My Bookings after I sign in
- When I send `GET /api/bookings/` or `POST /api/bookings/`
- Then the response is **401** and no booking data is returned or saved

**AC-7 (US-2): Create a booking via `/api/bookings/`**
- Given I am signed in as Sam and Dune's seat A1 is available
- When I send `POST /api/bookings/` with `{"seat": <A1's id>}`, even if I also send `"user": <Alex's id>`
- Then the response is **201** with the booking (id, movie Dune, seat A1, user Sam, booking date),
  and A1 is now `booked`
- Given A1 was already booked, through the seat page, `/api/seats/` or `/api/bookings/`
- When I send the same request
- Then the response is **409** with the same message as 002's AC-3, and no booking is made
- When the seat is missing or doesn't exist
- Then the response is **400** with an error for `seat`
- (Same rules as 002's AC-4, AC-5 and AC-6, through the same booking operation.)

**AC-8 (US-1, US-2): Order of the list**
- Given I booked A1 for Dune, then B2 for Up
- When I open My Bookings, or send `GET /api/bookings/`
- Then the Up booking (newest) comes first

**AC-9 (US-4): Cancel my booking**
- Given I am signed in and have booked A1 for Dune
- When I click "Cancel" on that booking in My Bookings and confirm, or send `DELETE /api/bookings/<id>/`
- Then the booking is gone (the API returns **204**; the page shows "Cancelled your booking of seat A1
  for Dune."), and A1 is `available` again, so anyone can book it
- When I try to cancel Alex's booking, through the page or the API
- Then the response is **404**, and Alex's booking is unchanged

**AC-10 (US-2): Bookings can't be edited**
- Given I have a booking
- When I send `PUT` or `PATCH /api/bookings/<id>/`
- Then the response is **405**, and the booking is unchanged. (To change seats, cancel and book again,
  so every seat change goes through the booking rules.)

## 4. Data
| Thing | Information | Rules |
|---|---|---|
| Booking | movie, seat, user, booking date | Only ever shown to, or cancelled by, its own user (AC-2, AC-3, AC-9). Never edited (AC-10). Cancelling deletes the booking and frees the seat (AC-9). |

## 5. API / UI behavior
| Action | Input | Success result | Failure result |
|---|---|---|---|
| My Bookings page (signed in) | — | my bookings, newest first; empty-state message if none | sign-in page if not signed in |
| Cancel booking (page, signed in) | booking | back to My Bookings with a message; seat free | 404 if not mine or missing |
| List bookings (API) | — | 200, my bookings, newest first | 401 |
| Get one booking (API) | id | 200, booking | 404 if not mine or missing; 401 |
| Create booking (API) | seat id | 201, booking | 409 taken; 400 bad or missing seat; 401 |
| Cancel booking (API) | id | 204 | 404 if not mine or missing; 401 |
| Edit booking (API) | — | — | 405 |

## 6. Out of scope
- Staff views of everyone's bookings in the app or API (staff use the Django admin site)
- Refunds, and rules on how late a booking can be cancelled (no showtimes exist: 002 out of scope)
- Editing a booking in place
- Paging the list

## 7. Open questions
- [x] AC-2 and AC-3 say users only see their own bookings. Why is this a **security** requirement,
      not just a feature choice? → Bookings link a person to where they'll be and when. Showing them
      to other users is Broken Access Control (OWASP A01), not a UI preference, and filtering only in
      the template would still leak them through `/api/bookings/<id>/`. Could staff see everyone's?
      → **Only in the Django admin site**, which already requires a staff login. The app and API
      treat staff like anyone else, so no extra AC is needed here.
- [x] 404 or 403 for someone else's booking? → **404** (AC-3).
- [x] Can `POST /api/bookings/` choose the movie? → **No.** The movie is the seat's movie (002's data
      rules), so the client sends only `seat`. A `movie` value in the request is ignored, like `user`.
