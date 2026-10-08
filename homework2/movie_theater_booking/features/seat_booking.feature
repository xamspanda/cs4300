Feature: Seat booking
  As a moviegoer I want to see which seats are free and book one.
  (specs/002-seat-booking)

  Background:
    Given the movie "Dune" exists
    And seat "A2" for "Dune" is booked by "alex"

  Scenario: See which seats are free
    # AC-1
    Given I am signed in as "sam"
    When I click "Book Now" for "Dune"
    Then I see seat "A2" as booked
    And I see seat "A1" as available

  Scenario: Book an available seat
    # AC-2
    Given I am signed in as "sam"
    When I open the seat booking page for "Dune"
    And I book seat "A1"
    Then I see "You booked seat A1 for Dune."
    And I see seat "A1" as booked
    And seat "A1" for "Dune" is booked by "sam"

  Scenario: Seat already taken
    # AC-3
    Given I am signed in as "sam"
    When I open the seat booking page for "Dune"
    And I book seat "A2"
    Then I see "Seat A2 for Dune is already booked."
    And seat "A2" for "Dune" is booked by "alex"

  Scenario: Must sign in to book
    # AC-8
    Given I am not signed in
    When I open the seat booking page for "Dune"
    Then I see "Sign in to book a seat"
    When I book seat "A1"
    Then I am sent to the sign-in page
    And seat "A1" for "Dune" is not booked
