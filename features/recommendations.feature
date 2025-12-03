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

    Scenario: Read an existing recommendation via the admin UI
        Given I remember the recommendation with base product "1001" and recommended product "2001"
        When I set the "Recommendation ID" to that recommendation id
        And I press the "Retrieve" button
        Then I should see the message "Success"
        And I should see "1001" in the "Base Product ID" field
        And I should see "2001" in the "Recommended Product ID" field
        And I should see "cross-sell" in the "Recommendation Type" dropdown
        And I should see "active" in the "Status" dropdown
        And I should see "0.85" in the "Confidence Score" field

    Scenario: Update an existing recommendation via the admin UI
        Given I remember the recommendation with base product "1001" and recommended product "2001"
        When I set the "Recommendation ID" to that recommendation id
        And I select "up-sell" in the "Recommendation Type" dropdown
        And I select "inactive" in the "Status" dropdown
        And I set the "Confidence Score" field to "0.92"
        And I press the "Update" button
        Then I should see the message "Recommendation updated"
        And I should see "up-sell" in the "Recommendation Type" dropdown
        And I should see "inactive" in the "Status" dropdown
        And I should see "0.92" in the "Confidence Score" field
        And the remembered recommendation should have type "up-sell", status "inactive", and confidence score "0.92"

    Scenario: Delete an existing recommendation via the admin UI
        Given I have the recommendation with base product "1001" and recommended product "2001"
        When I set the "Recommendation ID" to that recommendation id
        And I press the "Delete" button
        Then I should see the message "Recommendation deleted"
        And I should see "" in the "Base Product ID" field
        And I should see "" in the "Recommended Product ID" field
        And the remembered recommendation should not exist

    Scenario: List all recommendations via the admin UI
        Given the recommendation service is running
        And I am on the "Home Page"
        When I press the "List" button
        Then I should see the message "Success"
        And I should see at least 2 recommendations in the list
        And I should see a recommendation with base product "1001" and recommended product "2001" in the list
        And I should see a recommendation with base product "3001" and recommended product "4001" in the list
    
    Scenario: Filter recommendations by base_product_id and status via the admin UI
        Given the recommendation service is running
        And I am on the "Home Page"
        When I set the "Base Product ID" to "1001"
        And I set the "Status" to "Active"
        And I press the "Query" button
        Then I should see the message "Success"
        And I should see "1001" in the results table
        And I should not see "3001" in the results table
    
    Scenario: Filter recommendations by base_product_id via the admin UI
        Given the recommendation service is running
        And I am on the "Home Page"
        When I set the "Base Product ID" to "1001"
        And I press the "Query" button
        Then I should see the message "Success"
        And I should see "1001" in the results table
        And I should not see "3001" in the results table

    Scenario: Filter recommendations by status via the admin UI
        Given the recommendation service is running
        And I am on the "Home Page"
        When I set the "Status" to "active"
        And I press the "Query" button
        Then I should see the message "Success"
        And I should see "active" in the results table
        And I should not see "inactive" in the results table

    Scenario: Filter recommendations by recommendation_type via the admin UI
        Given the recommendation service is running
        And I am on the "Home Page"
        When I set the "Recommendation Type" to "cross-sell"
        And I press the "Query" button
        Then I should see the message "Success"
        And I should see "cross-sell" in the results table
        And I should not see "accessory" in the results table

    Scenario: Filter recommendations by minimum confidence_score via the admin UI
        Given the recommendation service is running
        And I am on the "Home Page"
        When I set the "Confidence Score" to "0.80"
        And I press the "Query" button
        Then I should see the message "Success"
        And I should see "0.85" in the results table
        And I should not see "0.70" in the results table

    Scenario: Filter recommendations by base_product_id and status via the admin UI
        Given the recommendation service is running
        And I am on the "Home Page"
        When I set the "Base Product ID" to "1001"
        And I set the "Status" to "active"
        And I press the "Query" button
        Then I should see the message "Success"
        And I should see "1001" in the results table
        And I should not see "3001" in the results table

    Scenario: Query all recommendations when no filter is provided via the admin UI
        Given the recommendation service is running
        And I am on the "Home Page"
        When I press the "Query" button
        Then I should see the message "Success"
        And I should see "1001" in the results table
        And I should see "3001" in the results table

    Scenario: Show an error when confidence_score is out of range via the admin UI
        Given the recommendation service is running
        And I am on the "Home Page"
        When I set the "Confidence Score" to "1.50"
        And I press the "Query" button
        Then I should see the message "Confidence Score must be a number between 0 and 1"
        And I should not see "1001" in the results table
        And I should not see "3001" in the results table

    Scenario: Create a new recommendation via the admin UI
        Given the recommendation service is running
        And I am on the "Home Page"
        When I set the "Base Product ID" field to "5001"
        And I set the "Recommended Product ID" field to "6001"
        And I select "cross-sell" in the "Recommendation Type" dropdown
        And I select "active" in the "Status" dropdown
        And I set the "Confidence Score" field to "0.95"
        And I set the "Base Product Price" field to "39.99"
        And I set the "Recommended Product Price" field to "14.99"
        And I press the "Create" button
        Then I should see the message "Recommendation created"
        And I press the "List" button
        And I should see a recommendation with base product "5001" and recommended product "6001" in the list
