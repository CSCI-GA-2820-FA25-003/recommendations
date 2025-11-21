Feature: The recommendation service back-end
    As a Merchandising Manager
    I need a RESTful recommendation service
    So that I can read existing product-to-product recommendations via the admin UI

    Background:
        Given the following recommendations exist
            | base_product_id | recommended_product_id | recommendation_type | status | confidence_score | base_product_price | recommended_product_price | base_product_description | recommended_product_description |
            | 1001            | 2001                   | cross-sell          | active | 0.85             | 19.99              | 9.99                      | Base product             | Accessory                       |
            | 3001            | 4001                   | accessory           | active | 0.70             | 29.99              | 4.99                      | Phone                    | Case                            |
        And the recommendation service is running
        And I am on the "Home Page"

    Scenario: View an existing recommendation via the admin UI
        Given I remember the recommendation with base product "1001" and recommended product "2001"
        When I set the "Recommendation ID" to that recommendation id
        And I press the "Retrieve" button
        Then I should see the message "Success"
        And I should see "1001" in the "Base Product ID" field
        And I should see "2001" in the "Recommended Product ID" field
        And I should see "cross-sell" in the "Recommendation Type" dropdown
        And I should see "active" in the "Status" dropdown
        And I should see "0.85" in the "Confidence Score" field
