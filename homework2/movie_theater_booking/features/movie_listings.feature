Feature: Movie listings
  As a moviegoer I want to see what's showing so that I can pick a movie.
  (specs/001-movie-listings)

  Scenario: Browse the movie list
    # AC-1
    Given the movie "Dune" exists with description "A noble family on a desert planet."
    And the movie "Up" exists with description "A house lifted by balloons."
    When I open the movie list page
    Then I see "Dune"
    And I see "A noble family on a desert planet."
    And I see "Up"
    And I see "A house lifted by balloons."
    And I see 2 "Book Now" buttons

  Scenario: No movies showing
    # AC-2
    Given no movies exist
    When I open the movie list page
    Then I see "No movies are showing right now"
