# Homework 2: Movie Theater Booking (Django)

A movie theater booking app with a REST API (Django REST Framework) and a
Bootstrap user interface (Django templates). Users browse movies, book seats,
check their booking history and cancel bookings, through the web pages or the API.

**Render URL:** <https://cs4300-o29m.onrender.com/> (free plan: the first request after idling can take about a minute)

**GitHub:** <https://github.com/xamspanda/cs4300/tree/main/homework2>

## Setup and running (DevEdu or any machine)

Requires Python 3.10 or newer. From the repository root:

```bash
cd homework2
python3 -m venv myenv --system-site-packages
source myenv/bin/activate
cd movie_theater_booking
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_movies          # optional: five sample movies
python manage.py createsuperuser      # optional: for /admin/
python manage.py runserver 0.0.0.0:3000
```

In DevEdu, click the **app** button next to the editor
(`https://app-<container>-<section>.devedu.io/`). Locally, open <http://localhost:3000/>.
Activate the virtual environment again in each new terminal.

## Tests

From `homework2/movie_theater_booking/` with the virtual environment active:

```bash
python manage.py test                                    # unit + integration (Django/DRF)
python manage.py behave                                  # BDD scenarios (Behave via behave-django)
coverage run manage.py test && coverage report           # coverage of app code
```

| Suite | Where | What |
|---|---|---|
| Unit + integration | `bookings/tests.py` (98 tests) | Models, the booking service, every API endpoint with status codes and JSON, every page, the admin site and the seed command |
| BDD | `features/*.feature` (9 scenarios) | Browsing movies, booking seats, booking history and cancelling, through the web pages |
| Coverage | `.coveragerc` | 100% of `bookings` app code (tests and migrations excluded) |

Each test's docstring names the acceptance criterion it proves (for example `AC-3`), from
the specs in `movie_theater_booking/specs/`.

## Using the app

| Page | URL | Notes |
|---|---|---|
| Movie list | `/` | Every movie with release date, length and **Book Now** |
| Seat booking | `/movies/<id>/book/` | 40 seats (A1–E8) per movie; click a green seat to book. Anyone can look; booking needs sign-in |
| My Bookings | `/bookings/` | Your bookings, newest first, with **Cancel** |
| Sign up / in / out | `/accounts/signup/`, `/accounts/login/` | Built-in Django accounts |
| Admin | `/admin/` | Needs a superuser |

### REST API

The browsable API is at `/api/`. Reading movies and seats needs no account. Everything else
needs a signed-in user: the site's session, or HTTP Basic auth (`curl -u user:pass`).

| Method | Endpoint | Result |
|---|---|---|
| GET | `/api/movies/` | 200, list of movies |
| POST | `/api/movies/` | 201 created; 400 with field errors (title and release date required, duration > 0); 401 if signed out |
| GET / PUT / PATCH / DELETE | `/api/movies/<id>/` | 200 / 200 / 200 / 204; 404 if missing |
| GET | `/api/seats/?movie=<id>&booking_status=available` | 200, seats with `booking_status` (`available` or `booked`); both filters optional; 400 for a bad movie id |
| GET | `/api/seats/<id>/` | 200 / 404 |
| POST | `/api/seats/<id>/book/` | 201 with the booking; **409** if already booked; 404; 401 |
| GET | `/api/bookings/` | 200, **only your own** bookings, newest first; 401 |
| POST | `/api/bookings/` with `{"seat": <id>}` | 201; 409 if taken; 400 for a missing or bad seat; 401 |
| GET / DELETE | `/api/bookings/<id>/` | 200 / 204 (cancel, frees the seat); **404 for someone else's booking** |
| PUT / PATCH | `/api/bookings/<id>/` | 405: cancel and rebook instead |
| POST / PUT / PATCH / DELETE | `/api/seats/...` | 405: seats change only by booking |

Example:

```bash
curl -u sam:password -X POST http://localhost:3000/api/seats/12/book/
curl -u sam:password http://localhost:3000/api/bookings/
```

## Design decisions

- **Seats belong to a movie.** The assignment's Seat (seat number, booking status) has no movie,
  so availability would otherwise be global. Each movie gets its own 40 seats automatically when
  it is created (a `post_save` signal), like one screening per movie.
- **One booking operation.** `bookings/services.py` has `book_seat()` and `cancel_booking()`. The
  seat page, `/api/seats/<id>/book/`, `/api/bookings/` and the admin site all go through them, so
  the rules can't drift apart.
- **No double booking, even under a race.** A database unique constraint on `Booking.seat` makes
  the database refuse a second booking of a seat. `book_seat()` turns that refusal into a clean
  "already booked" error (409 in the API), never a 500.
- **The booking row is the truth.** `Seat.booking_status` is a stored copy, so the seat list can
  be filtered. Only the service writes it, in the same transaction as the booking change. It is
  read-only in the admin site and the API.
- **Privacy.** A booking's user is always the signed-in user (a `user` in the request is ignored),
  and other users' bookings are 404, not 403, so their existence isn't revealed.
- **Who can change movies.** Any signed-in user can create, edit or delete movies through the
  API, so a grader can try full CRUD after signing up. Deleting a movie also deletes its seats and
  everyone's bookings for it, so a real theater would limit this to staff.
- **Known limits.** Double booking is prevented by the database constraint, but there is no
  multi-threaded test of two truly simultaneous requests (SQLite's in-memory test database can't
  share one between threads). On SQLite, `transaction_mode: IMMEDIATE` makes concurrent bookings
  queue for the write lock. There is no rate limiting on sign-in.

## Project structure

```
homework2/
├── README.md                      ← this file
└── movie_theater_booking/         ← Django project root (manage.py)
    ├── movie_theater_booking/     ← settings.py, urls.py, wsgi.py
    ├── bookings/                  ← the app
    │   ├── models.py              ← Movie, Seat, Booking
    │   ├── services.py            ← book_seat / cancel_booking (the booking rules)
    │   ├── signals.py             ← new movie → 40 seats
    │   ├── serializers.py         ← Movie/Seat/Booking serializers
    │   ├── views.py               ← MovieViewSet, SeatViewSet, BookingViewSet + page views
    │   ├── urls.py                ← /api/ router and page routes
    │   ├── admin.py
    │   ├── management/commands/seed_movies.py
    │   ├── templates/bookings/    ← base, movie_list, seat_booking, booking_history
    │   ├── templates/registration/← login, signup
    │   └── tests.py
    ├── features/                  ← Behave .feature files and steps/
    ├── specs/                     ← spec-driven development: spec, plan, tasks per feature
    ├── AGENTS.md, prompts/, SDD-TEMPLATE-README.md  ← the course's SDD template
    ├── AI-USAGE.md                ← AI usage log
    ├── requirements.txt, build.sh, render.yaml, .coveragerc
```

## Deploying to Render

1. Push to GitHub, then on [render.com](https://render.com) choose **New → Web Service** and
   connect `xamspanda/cs4300`.
2. Settings:
   - **Root Directory:** `homework2/movie_theater_booking`
   - **Runtime:** Python 3
   - **Build Command:** `./build.sh` (installs, `collectstatic`, `migrate`, `seed_movies`)
   - **Start Command:** `gunicorn movie_theater_booking.wsgi:application`
   - **Instance type:** Free
3. Environment variables: `DJANGO_SECRET_KEY` set to a long random value, which you can make with
   `python -c "import secrets; print(secrets.token_urlsafe(50))"`. Render sets `RENDER` and
   `RENDER_EXTERNAL_HOSTNAME` itself; the settings use them to turn off `DEBUG`, allow the host
   and trust its HTTPS origin.
4. Deploy. This app is live at <https://cs4300-o29m.onrender.com/>.

(`render.yaml` describes the same service as a Blueprint, if you prefer that route.)

The free plan uses SQLite on an ephemeral disk: the sample movies come back on every deploy, but
accounts and bookings are reset when the service restarts or redeploys. That's fine for a demo;
a real deployment would use Render PostgreSQL.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | a development-only key (required on Render) | Django signing key; never committed |
| `DJANGO_DEBUG` | `true` locally, `false` on Render | Debug pages |
| `RENDER`, `RENDER_EXTERNAL_HOSTNAME` | set by Render | Production settings and allowed host |

## AI usage

See [`movie_theater_booking/AI-USAGE.md`](movie_theater_booking/AI-USAGE.md) for the full log.

- **Tool:** Claude Code (Anthropic), model Claude Opus 5.5; one review pass by a Claude Sonnet 5.5
  subagent.
- **Used for:** following the course's spec-driven development template: finishing the specs
  for features 002 and 003 from my design decisions, drafting the plans and task lists, writing
  the code and tests one task at a time (test first), the seed command, deployment files and this
  README, plus an independent review of the code against the specs.
- **How I used the output:** I made the design decisions (seats belong to a movie; sign-up and
  sign-in pages; cancellation in My Bookings). I reviewed each commit that was created with
  AI assistance, ran the tests and tried the app myself. I also looked at the tests to see if
  they were valid and useful.
