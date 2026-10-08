# AI Usage Log

Course policy: any use of AI (for ideas, text, code or anything else) must be cited in your
README, saying **which tool**, **what it was used for**, and **how you used the output**.
Keep this log as you go, then copy the summary into your README.

> 📖 **Book:** "Record where you used AI and how you verified it", [§13.2.10](https://www.swebook.org/chapters/13-ai-across-the-lifecycle/index.html#13210-the-team-project-appendix-a).

## Summary (paste into README)
- **Tool:** Claude Code (Anthropic), model Claude Opus 5.5 (`claude-opus-5-5`), used in place
  of Codex with this template's `AGENTS.md` rules; one independent review pass by a Claude
  Sonnet 5.5 subagent that did not write the code (prompt 5).
- **Used for:** finishing the specs for 002 and 003 from my design decisions, drafting all
  three plans and task lists, test-first implementation of every task, the seed command,
  Render deployment files, the README, and reviewing the code against the specs.
- **How I used the output:** I made the design decisions (seats belong to a movie; sign-up and
  sign-in pages; users can cancel their own bookings in My Bookings; one commit per task).
  I reviewed each commit that was created with AI assistance, ran the tests and tried the app
  myself. I also looked at the tests to see if they were valid and useful.

## Log
| Date | Feature / task | What I asked the AI | What I kept, changed or rejected |
|---|---|---|---|
| 2026-10-08 | Setup | Read the HW2 PDF and the SDD template; create the Django project, `bookings` app and venv; copy the template in | Kept. Django pinned to 5.2 LTS (not 6.x) so it runs on older DevEdu Python versions; secrets read from environment variables |
| 2026-10-08 | Decisions | AI asked me four questions before writing 002/003 specs | I chose: seats per movie, login + sign-up pages, cancellation allowed, AI commits per task and I push |
| 2026-10-08 | 001 spec/plan/tasks | Resolve the open question; adjust for a public deployment | Kept the example's field rules; added AC-10 (anonymous clients can read but not change movies, 401) |
| 2026-10-08 | 002 spec/plan/tasks | Finish the spec from my decisions | Seat gets a movie FK; Booking row is the source of truth with a DB unique constraint on seat; 409 for a taken seat; seats auto-created A1–E8; AC-8 to AC-14 added |
| 2026-10-08 | 003 spec/plan/tasks | Finish the spec | 404 (not 403) for others' bookings; cancel via page + `DELETE`; no edits (405); newest first; AC-5 to AC-10 added |
| 2026-10-08 | 001 T1–T16 | Implement test first | Movie model, CRUD API, Bootstrap base + movie list, Behave. T7–T10 were verification tests (ModelViewSet already did it) |
| 2026-10-08 | 002 T1–T16 | Implement test first | Seat/Booking, `services.book_seat`, seats API, auth pages, seat grid page, admin, Behave |
| 2026-10-08 | 003 T1–T9 | Implement test first | `cancel_booking`, `BookingViewSet`, My Bookings page, admin delete through the service, Behave |
| 2026-10-08 | Deploy | Seed command, `build.sh`, `render.yaml`, README | Smoke-tested production settings locally with gunicorn; Render deploy itself must be done from my Render account |
| 2026-10-08 | Review (prompt 5) | Fresh subagent (didn't write the code) reviewed every AC against the code and tests | It found 500s on odd input (`?movie=²`, huge ids), seat status drifting after deleting a user or a stale double cancel, exposed password-reset pages, and test gaps |
| 2026-10-08 | Review fixes R1–R3 | Fix each finding test first | Safe id parsing and 400s; status recomputed from bookings everywhere (`post_delete` signal); only login/logout routed; duration ≤ 1440; SQLite IMMEDIATE transactions; 12 new tests. Not done: a true multi-threaded race test (noted in README) |
