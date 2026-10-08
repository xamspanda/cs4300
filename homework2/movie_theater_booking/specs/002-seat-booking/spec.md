# Spec: Seat booking

**Status:** Implemented
**Author:** Laura  **Date:** 2026-10-08

## 1. Problem
A moviegoer who has picked a movie needs to see which seats are free and reserve one.
(Homework 2, or HW2, §1 "Book seats via the API"; §3.3 `SeatViewSet` "for seat availability and booking";
§3.5 `/api/seats/`; template `seat_booking.html`.)

## 2. User stories
- **US-1:** As a moviegoer, I want to see which seats are available for a movie, so that I can choose one.
- **US-2:** As a moviegoer, I want to book an available seat, so that it's reserved for me.
- **US-3:** As an API client, I want to check seat availability and book seats through `/api/seats/`.
  (HW2 also has `/api/bookings/` create bookings; see AC-6 and feature 003.)
- **US-4:** As a moviegoer, I want to create an account and sign in, so that my bookings are mine.
- **US-5:** As the theater, I want every movie to come with its seats, so that it can be booked as
  soon as it is listed.

One booking is one seat. To sit with friends, a moviegoer books each seat in turn.

## 3. Acceptance criteria

**AC-1 (US-1): Seat availability page**
- Given the movie "Dune" and seats A1–A5, where A2 is already booked
- When I click "Book Now" for Dune
- Then I see the seat booking page for Dune, with A2 shown as unavailable and the others as available
- (This is where "Book Now" on the movie list, disabled in 001, becomes a real link.)

**AC-2 (US-2): Book an available seat**
- Given I am signed in and seat A1 is available for Dune
- When I book A1
- Then I stay on Dune's seat booking page and see "You booked seat A1 for Dune."
- And a booking of A1 for Dune exists with me as its user and today's date, and A1 is shown as
  unavailable from now on (on the page and in `/api/seats/`)

**AC-3 (US-2): Seat already taken**
- Given seat A2 is already booked for Dune
- When I try to book A2
- Then no booking is made. The page shows "Seat A2 for Dune is already booked." and the API returns
  **409 Conflict** with that message in `detail`

**AC-4 (US-2): No double booking, even at the same moment**
- Given seat A1 is available for Dune
- When two requests to book A1 for Dune arrive at the same moment, or code saves a second booking
  of A1 for Dune without going through the page or API checks
- Then only one booking of A1 for Dune exists. The second save is refused, and a user or client
  making the second request gets the same answer as AC-3 (never a 500 error)
- (Checking "is it taken?" before saving isn't enough: two requests can both pass the check before
  either one saves. The database itself has to refuse the duplicate.)
- 📖 **Book:** the data store owns integrity constraints and concurrency control, [§7.2.1 The Shared-Data Pattern](https://www.swebook.org/chapters/07-architectural-patterns/index.html#721-the-shared-data-pattern).

**AC-5 (US-2, US-3): The booking belongs to whoever is signed in**
- Given I am signed in as Sam
- When I book a seat through the page or the API, even if the request data names another user
- Then the booking's user is Sam
- 📖 **Book:** [§11.2.1 A01: Broken Access Control](https://www.swebook.org/chapters/11-software-security/index.html#1121-a01-broken-access-control)

**AC-6 (US-2, US-3): Same rules everywhere**
- Given seat A1 has been booked for Dune through the seat booking page
- When anyone tries to book A1 for Dune through `/api/seats/` (or the other way round)
- Then it is refused exactly as in AC-3, because both follow one set of booking rules
- (003 adds `/api/bookings/` as a third way to book. It must follow the same rules: 003's AC-7.)

**AC-7 (UI): Consistent layout**
- Given the seat booking page for a movie
- When it renders
- Then it extends `base.html`, with the same navbar as the movie list

**AC-8 (US-2, US-4): Not signed in**
- Given I am not signed in
- When I open Dune's seat booking page
- Then I can see the seats, but instead of booking I see a prompt to sign in
- When I submit a booking anyway, or send `POST /api/seats/<id>/book/`
- Then no booking is made: the page sends me to the sign-in page (and back to Dune's seats after I
  sign in), and the API returns **401**

**AC-9 (US-1, US-2): Missing movie or seat**
- Given no movie with id 9999 and no seat with id 9999 exist
- When I open the seat booking page for movie 9999, or send `POST /api/seats/9999/book/`
- Then the response is **404**
- When I submit the page for Dune with a seat id that isn't one of Dune's seats
- Then no booking is made, and the page shows "That seat does not exist for this movie."

**AC-10 (US-3): List seats and availability via API**
- Given Dune has seats A1–A3 where A2 is booked, and "Up" has its own seats
- When a client sends `GET /api/seats/?movie=<Dune's id>`
- Then the response is 200 with only Dune's seats, each with id, movie, seat number and booking status
  (`available` or `booked`), A2 being `booked`
- When a client adds `&booking_status=available`
- Then A2 is left out
- When `movie` is not a whole number, or `booking_status` is not `available` or `booked`
- Then the response is 400

**AC-11 (US-3): Book through the seats API**
- Given I am signed in and Dune's seat A1 is available
- When I send `POST /api/seats/<A1's id>/book/`
- Then the response is **201** with the new booking (id, movie, seat, user, booking date), and A1's
  booking status is now `booked`

**AC-12 (US-3, US-5): Seats can't be created, changed or deleted through the API**
- Given a seat exists
- When a signed-in client sends `POST /api/seats/`, or `PUT`/`PATCH`/`DELETE /api/seats/<id>/`
- Then the response is **405**, and the seat is unchanged. (A seat changes status only by booking
  or cancelling. Seats come with their movie: AC-13.)

**AC-13 (US-5): A new movie comes with its seats**
- Given no movies exist
- When a movie is created (through the API or the admin site)
- Then it has 40 seats, rows A–E with seats 1–8 (A1 … E8), all `available`

**AC-14 (US-4): Sign up, sign in and sign out**
- Given I have no account
- When I sign up with a new username and a valid password (twice)
- Then I am signed in and returned to the movie list, and the navbar shows my username and "Sign out"
- When I sign up with a username that is taken, or two passwords that don't match
- Then I see the error and no account is made
- When I sign out, then sign in again with my username and password
- Then I am signed in again

## 4. Data
| Thing | Information | Rules |
|---|---|---|
| Seat | movie, seat number, booking status | Each seat belongs to **one movie** (one screening). Seat number is a row letter A–E and a number 1–8, unique within its movie. Booking status is `available` or `booked`, stored on the seat, and changed only by booking or cancelling. |
| Booking | movie, seat, user, booking date | User is always the signed-in user (AC-5). Movie is the seat's movie. At most one booking per seat, enforced by the database (AC-4). Booking date is set when the booking is made. |

## 5. API / UI behavior
| Action | Input | Success result | Failure result |
|---|---|---|---|
| View seats for a movie (page) | movie | page with every seat, booked ones unavailable | 404 if the movie doesn't exist |
| Book a seat (page, signed in) | seat | back to the seat page with a success message | "already booked" or "does not exist for this movie" message; sign-in page if not signed in |
| List seats (API) | optional `movie`, `booking_status` | 200, list | 400 if `movie` is not a whole number |
| Get one seat (API) | id | 200, seat | 404 |
| Book a seat (API, signed in) | seat id in the URL | 201, booking | 409 taken; 404 no such seat; 401 not signed in |
| Change seats (API) | — | — | 405 |
| Sign up / sign in / sign out (page) | username, password | signed in (or out), back to movie list | form errors |

## 6. Out of scope
- Payments, prices, tickets
- Booking several seats in one request; seat maps with aisles or accessibility seating
- Holding a seat for a few minutes while the user decides
- Showtimes or several screenings of one movie (a movie *is* its one screening here)
- Password reset and email confirmation
- Cancelling a booking: feature 003 (My Bookings)

## 7. Open questions
- [x] **The assignment's Seat model has no movie field.** Is a seat booked for *every* movie, or
      is availability per movie? → **Per movie.** Seat gets a movie, so each movie has its own
      40 seats, like one screening in one auditorium. Booking a seat for Dune leaves Up's seats
      alone. Booking still records its movie, as the assignment asks; it is always the seat's movie.
- [x] **One source of truth for "is this seat taken?"** → (1) Availability is per seat, and a seat
      belongs to one movie, so it is per (movie, seat). (2) **The Booking is the source of truth**:
      a seat is taken exactly when a booking for it exists, and the database refuses a second one.
      (3) The stored booking status is a copy kept so the seat list can show and filter it cheaply.
      Only the booking module writes it, recomputing it from the bookings in the same database
      transaction as every booking change. Any other way a booking disappears (the admin site, or
      deleting a user) triggers the same recomputation. The admin site shows status as read-only and
      can't add bookings. Deleting a movie
      deletes its seats and bookings together. (4) AC-2 and AC-11 check the status after booking,
      and 003's AC-9 checks it after cancelling.
- [x] **Where does "book a seat" live?** → One function in its own module. The seat page,
      `/api/seats/<id>/book/` and `/api/bookings/` (003) all call it with the signed-in user and the
      seat. It saves the booking, lets the database refuse a seat that is already taken (turning that
      into the "already booked" error), and updates the status. A second copy of these
      rules could drift (for example, forget the status update), and AC-6 would fail.
- [x] Can a booking be cancelled? → **Yes, by its own user, in feature 003** (My Bookings and
      `DELETE /api/bookings/<id>/`). It uses the same module as booking.
- [x] What status code for a taken seat? → **409 Conflict**: the request is valid but conflicts with
      the seat's current state. 400 would suggest the client sent bad data.
