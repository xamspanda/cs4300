Feature: Booking history
  As a moviegoer I want to see and cancel my bookings, and keep them private.
  (specs/003-booking-history)

  Background:
    Given the movie "Dune" exists
    And the movie "Up" exists

  Scenario: See my bookings
    # AC-1, AC-2
    Given seat "A1" for "Dune" is booked by "sam"
    And seat "C7" for "Up" is booked by "alex"
    And I am signed in as "sam"
    When I open My Bookings
    Then I see "Dune"
    And I see "A1"
    And I see today's date
    And I do not see "C7"

  Scenario: No bookings yet
    # AC-5
    Given I am signed in as "sam"
    When I open My Bookings
    Then I see "You have no bookings yet."

  Scenario: Cancel a booking
    # AC-9
    Given seat "A1" for "Dune" is booked by "sam"
    And I am signed in as "sam"
    When I open My Bookings
    And I cancel my booking of seat "A1" for "Dune"
    Then I see "Cancelled your booking of seat A1 for Dune."
    And I see "You have no bookings yet."
    And seat "A1" for "Dune" is not booked
