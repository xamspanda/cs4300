# Spec: Movie listings

**Status:** Reviewed
**Author:** Laura  **Date:** 2026-10-08

## 1. Problem
Moviegoers need to see what's showing before they can book a seat. Staff need to add, update
and remove movies. (Homework 2, or HW2, §1 and §3.3: "View movie listings", and `MovieViewSet` "for CRUD operations",
where CRUD means create, read, update, delete.)

## 2. User stories
> 📖 **Book:** [§3.4.1 Guidelines for Effective User Stories](https://www.swebook.org/chapters/03-user-requirements/index.html#341-guidelines-for-effective-user-stories) (INVEST: Independent, Negotiable, Valuable, Estimable, Small, Testable)

Each user story (US-#) is numbered so the acceptance criteria can trace back to it.

- **US-1:** As a moviegoer, I want to see a list of movies, so that I can pick one to watch.
- **US-2:** As a moviegoer, I want to see a movie's details (description, release date,
  duration), so that I can decide whether to watch it.
- **US-3:** As an API client, I want to create, read, update and delete movies, so that the
  listings can be managed.
- **US-4:** As the theater, I want only signed-in users to change the listings, so that an
  anonymous visitor to the public site can't erase them.

## 3. Acceptance criteria
Each acceptance criterion (AC-#) names the user story it checks, e.g., AC-1 (US-1).

> 📖 **Book:** [§3.4.1 Given / When / Then](https://www.swebook.org/chapters/03-user-requirements/index.html#given--when--then-writing-acceptance-criteria-as-scenarios). AC-6 tests the boundary (duration 0): [§10.4.2 boundary values](https://www.swebook.org/chapters/10-testing/index.html#1042-boundary-value-coverage).

**AC-1 (US-1): List movies in the UI**
- Given the movies "Dune" and "Up" exist
- When I open the movie list page
- Then I see both titles, each with its description and a "Book Now" button
- (The button is shown but disabled until feature 002 adds the seat booking page. 002 makes it a link.)

**AC-2 (US-1): Empty state**
- Given no movies exist
- When I open the movie list page
- Then I see "No movies are showing right now" instead of an empty list

**AC-3 (US-2): Movie details shown**
- Given "Dune" has a release date of 2021-10-22 and a duration of 155 minutes
- When I view the movie list
- Then Dune's release date and duration are shown in a readable format

**AC-4 (US-3): List via API**
- Given two movies exist
- When a client sends `GET /api/movies/`
- Then the response is 200 with a JSON list of 2 movies, each with id, title, description,
  release date and duration

**AC-5 (US-3): Create via API**
- Given I am signed in and have valid movie data
- When a client sends `POST /api/movies/`
- Then the response is 201 and the movie appears in `GET /api/movies/`

**AC-6 (US-3): Reject invalid data**
- Given I am signed in and have movie data with a missing title, a missing release date, or a duration of 0 or less
- When a client sends `POST /api/movies/`
- Then the response is 400 with an error for that field, and nothing is saved

**AC-7 (US-3): Update and delete**
- Given I am signed in and a movie exists
- When a client sends `PUT`/`PATCH /api/movies/<id>/`, then `DELETE /api/movies/<id>/`
- Then the update returns 200 with the new values, the delete returns 204, and the movie is gone

**AC-8 (US-3): Get one movie, or a missing one**
- Given "Dune" exists and no movie with id 9999 exists
- When a client sends `GET /api/movies/<Dune's id>/`, then `GET /api/movies/9999/`
- Then the first response is 200 with Dune's fields, and the second is 404

**AC-9 (UI): Consistent, responsive layout**
- Given the movie list page
- When it renders
- Then it extends `base.html` (Bootstrap), with a navbar linking to Movies
- (002 and 003 each add the same criterion, with its own test, for their page. 003 adds the
  My Bookings link to the navbar once that page exists.)

**AC-10 (US-4): Anonymous clients can read but not change**
- Given I am not signed in and "Dune" exists
- When I send `GET /api/movies/`, then `POST /api/movies/`, `PATCH /api/movies/<id>/` and `DELETE /api/movies/<id>/`
- Then the `GET` returns 200, each change returns 401, and Dune is unchanged

## 4. Data
| Thing | Information | Rules |
|---|---|---|
| Movie | title | **Required**; at most 200 characters |
| Movie | description | Optional (may be blank) |
| Movie | release date | **Required**; a valid date |
| Movie | duration | **Required**; whole minutes, greater than 0 |

## 5. API / UI behavior
| Action | Input | Success result | Failure result |
|---|---|---|---|
| View movie list page | — | page with every movie and a "Book Now" button | — |
| List movies (API) | — | 200, list | — |
| Get one movie (API) | id | 200, movie | 404 |
| Create movie (API, signed in) | title, description, release date, duration | 201, movie | 400 + field errors; 401 if not signed in |
| Update movie (API, signed in) | id + fields | 200, movie | 400 / 404; 401 if not signed in |
| Delete movie (API, signed in) | id | 204 | 404; 401 if not signed in |

## 6. Out of scope
- Showtimes, theaters, posters, ratings, search
- Restricting movie create/update/delete to *staff*. Any signed-in user may change movies (AC-10),
  so a grader can try the full CRUD API after signing up. Noted in the README.

## 7. Open questions
- [x] Duration in minutes or as `HH:MM`? → **Integer minutes.** Simpler to validate and test.
- [x] Order of the list? → **By release date, newest first.**
- [x] Which fields are required? → **Keep the example's rules.** Title, release date and duration
      are required; description is optional. This theater lists only movies it is showing, so every
      listed movie has a release date. A missing or invalid required field returns 400 with an error
      for that field (AC-6: `test_create_movie_missing_title_400`,
      `test_create_movie_missing_release_date_400`, `test_create_movie_zero_duration_400`).
- [x] Who may change movies? → **Signed-in users** (AC-10). The deployed site is public.
