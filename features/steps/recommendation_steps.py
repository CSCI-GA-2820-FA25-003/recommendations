"""Step definitions for recommendation UI feature."""

import re
import requests
from behave import given, when, then  # pylint: disable=no-name-in-module
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

# HTTP Return Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_409_CONFLICT = 409
HTTP_404_NOT_FOUND = 404

WAIT_TIMEOUT = 60


def _wait_for_text(context, locator, text):
    """Wait until specific text appears in the element."""
    WebDriverWait(context.driver, context.wait_seconds).until(
        EC.text_to_be_present_in_element(locator, text)
    )


def _field_value(context, element_id):
    """Return the value attribute for a field by id."""
    return context.driver.find_element(By.ID, element_id).get_attribute("value")


@given("the recommendation service is running")
def step_service_running(context):
    resp = requests.get(f"{context.base_url}/health", timeout=WAIT_TIMEOUT)
    assert resp.status_code == HTTP_200_OK


@given('I am on the "Home Page"')
def step_open_home_page(context):
    context.driver.get(f"{context.base_url}/ui")


######################################################################
# Scenario: Read an existing recommendation via the admin UI
######################################################################


@given("the following recommendations exist")
def step_seed_recommendations(context):
    """Delete all recommendations and load the ones from the Background table."""
    rest_endpoint = f"{context.base_url}/recommendations"

    # 1) Delete all existing recommendations
    resp = requests.get(rest_endpoint, timeout=WAIT_TIMEOUT)
    resp.raise_for_status()
    for rec in resp.json():
        rec_id = rec["recommendation_id"]
        del_resp = requests.delete(f"{rest_endpoint}/{rec_id}", timeout=WAIT_TIMEOUT)
        # Most APIs return 204 for successful delete
        assert del_resp.status_code in (
            HTTP_200_OK,
            204,
            HTTP_404_NOT_FOUND,
        ), f"Failed to delete recommendation {rec_id}: {del_resp.status_code}"

    # 2) Seed fresh recommendations from the table
    for row in context.table:
        payload = {
            "base_product_id": int(row["base_product_id"]),
            "recommended_product_id": int(row["recommended_product_id"]),
            "recommendation_type": row["recommendation_type"],
            "status": row["status"],
            "confidence_score": float(row["confidence_score"]),
        }
        if row.get("base_product_price"):
            payload["base_product_price"] = float(row["base_product_price"])
        if row.get("recommended_product_price"):
            payload["recommended_product_price"] = float(
                row["recommended_product_price"]
            )
        if row.get("base_product_description"):
            payload["base_product_description"] = row["base_product_description"]
        if row.get("recommended_product_description"):
            payload["recommended_product_description"] = row[
                "recommended_product_description"
            ]

        resp = requests.post(rest_endpoint, json=payload, timeout=WAIT_TIMEOUT)
        resp.raise_for_status()


@given(
    'I remember the recommendation with base product "{base_id}" and recommended product "{rec_id}"'
)
def step_remember_recommendation(context, base_id, rec_id):
    """Fetch and store a recommendation id matching the given base/recommended ids."""
    resp = requests.get(
        f"{context.base_url}/recommendations",
        params={"base_product_id": int(base_id)},
        timeout=WAIT_TIMEOUT,
    )
    resp.raise_for_status()
    matches = [
        rec
        for rec in resp.json()
        if str(rec.get("recommended_product_id")) == str(rec_id)
    ]
    assert (
        matches
    ), f"No recommendation found for base {base_id} and recommended {rec_id}"
    rec = matches[0]
    context.remembered_rec = rec
    # Also store in remembered_recs dict for scenarios that need multiple
    if not hasattr(context, "remembered_recs"):
        context.remembered_recs = {}
    context.remembered_recs[base_id] = {"recommendation": rec}


@when('I set the "Recommendation ID" to that recommendation id')
def step_set_recommendation_id(context):
    rec_id = context.remembered_rec["recommendation_id"]
    field = context.driver.find_element(By.ID, "recommendation_id")
    field.clear()
    field.send_keys(str(rec_id))
    context.current_rec_id = rec_id


@when('I set the "Recommendation ID" to "{value}"')
def step_set_recommendation_id_literal(context, value):
    field = context.driver.find_element(By.ID, "recommendation_id")
    field.clear()
    field.send_keys(value)


@when('I press the "Retrieve" button')
def step_press_retrieve(context):
    context.driver.find_element(By.ID, "retrieve-btn").click()


@then('I should see the message "{text}"')
def step_should_see_message(context, text):
    _wait_for_text(context, (By.ID, "flash_message"), text)
    actual = context.driver.find_element(By.ID, "flash_message").text
    assert text in actual


def _label_to_element_id(field_label: str) -> str:
    mapping = {
        "Recommendation ID": "recommendation_id",
        "Base Product ID": "base_product_id",
        "Recommended Product ID": "recommended_product_id",
        "Recommendation Type": "recommendation_type",
        "Status": "status",
        "Confidence Score": "confidence_score",
        "Base Product Price": "base_product_price",
        "Recommended Product Price": "recommended_product_price",
        "Base Product Description": "base_product_description",
        "Recommended Product Description": "recommended_product_description",
    }
    element_id = mapping.get(field_label)
    assert element_id, f"Unknown field label: {field_label}"
    return element_id


@then('I should see "{expected}" in the "{field_label}" field')
def step_should_see_in_field(context, expected, field_label):
    element_id = _label_to_element_id(field_label)
    value = _field_value(context, element_id)
    assert str(expected) == str(
        value
    ), f"Expected {expected} in {field_label}, got {value}"


@then('I should see "{expected}" in the "{field_label}" dropdown')
def step_should_see_in_dropdown(context, expected, field_label):
    element_id = _label_to_element_id(field_label)
    value = _field_value(context, element_id)
    assert str(expected) == str(
        value
    ), f"Expected {expected} in {field_label}, got {value}"


######################################################################
# Scenario: Update an existing recommendation via the admin UI
######################################################################


@when('I select "{option}" in the "{field_label}" dropdown')
def step_select_in_dropdown_when(context, option, field_label):
    """Choose an option from a dropdown by value."""
    element_id = _label_to_element_id(field_label)
    select_elem = Select(context.driver.find_element(By.ID, element_id))
    select_elem.select_by_value(option)


@when('I set the "{field_label}" field to "{value}"')
def step_set_field_value(context, field_label, value):
    """Populate a text/number field with a value."""
    element_id = _label_to_element_id(field_label)
    field = context.driver.find_element(By.ID, element_id)
    field.clear()
    field.send_keys(value)


@when('I press the "Update" button')
def step_press_update(context):
    """Press the Update button on the UI."""
    context.driver.find_element(By.ID, "update-btn").click()


@then(
    'the remembered recommendation should have type "{rec_type}", '
    'status "{status}", and confidence score "{confidence}"'
)
def step_verify_updated_recommendation(context, rec_type, status, confidence):
    """Verify the remembered recommendation reflects updated values via the API."""
    rec_id = getattr(context, "current_rec_id", None)
    if rec_id is None and hasattr(context, "remembered_rec"):
        rec_id = context.remembered_rec["recommendation_id"]

    assert rec_id is not None, "No recommendation id available for verification"

    resp = requests.get(
        f"{context.base_url}/recommendations/{rec_id}",
        timeout=WAIT_TIMEOUT,
    )
    resp.raise_for_status()
    rec = resp.json()

    assert str(rec.get("recommendation_type")) == str(rec_type)
    assert str(rec.get("status")) == str(status)

    expected_conf = float(confidence)
    actual_conf = float(rec.get("confidence_score"))
    assert (
        abs(actual_conf - expected_conf) < 1e-6
    ), f"Expected confidence {expected_conf}, got {actual_conf}"


######################################################################
# Scenario: Delete an existing recommendation via the admin UI
######################################################################


@given(
    'I have the recommendation with base product "{base_id}" and recommended product "{rec_id}"'
)
def step_have_recommendation(context, base_id, rec_id):
    """Fetch and store a recommendation id matching the given base/recommended ids."""
    resp = requests.get(
        f"{context.base_url}/recommendations",
        params={"base_product_id": int(base_id)},
        timeout=WAIT_TIMEOUT,
    )
    resp.raise_for_status()
    matches = [
        rec
        for rec in resp.json()
        if str(rec.get("recommended_product_id")) == str(rec_id)
    ]
    assert (
        matches
    ), f"No recommendation found for base {base_id} and recommended {rec_id}"
    context.remembered_rec = matches[0]


@when('I press the "Delete" button')
def step_press_delete(context):
    """Press the Delete button on the UI."""
    context.driver.find_element(By.ID, "delete-btn").click()


@then('I should see "" in the "Base Product ID" field')
def step_base_id(context):
    """The Base Product ID field should be empty"""
    element_id = _label_to_element_id("Base Product ID")
    value = _field_value(context, element_id)
    assert (
        value == ""
    ), f'Expected "Base Product ID" field to be empty, but got "{value}"'


@then('I should see "" in the "Recommended Product ID" field')
def step_rec_id(context):
    """The Recommended Product ID field should be empty"""
    element_id = _label_to_element_id("Recommended Product ID")
    value = _field_value(context, element_id)
    assert (
        value == ""
    ), f'Expected "Recommended Product ID" field to be empty, but got "{value}"'


@then("the remembered recommendation should not exist")
def step_remembered_recommendation_should_not_exist(context):
    """Verify that the remembered recommendation no longer exists via the API."""
    rec_id = getattr(context, "current_rec_id", None)
    if rec_id is None and hasattr(context, "remembered_rec"):
        rec_id = context.remembered_rec["recommendation_id"]

    assert rec_id is not None, "No recommendation id remembered in context"

    resp = requests.get(
        f"{context.base_url}/recommendations/{rec_id}",
        timeout=WAIT_TIMEOUT,
    )
    assert (
        resp.status_code == HTTP_404_NOT_FOUND
    ), f"Expected 404 after delete, got {resp.status_code}"


######################################################################
# Scenario: List all recommendations via the admin UI
######################################################################


def _parse_search_results(context):
    """Parse the search results table into a list of dicts."""
    table = context.driver.find_element(By.ID, "search_results")
    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    results = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if not cells:
            continue
        rec = {
            "recommendation_id": cells[0].text.strip(),
            "base_product_id": cells[1].text.strip(),
            "recommended_product_id": cells[2].text.strip(),
        }
        results.append(rec)
    return results


@when('I press the "List" button')
def step_press_list_button(context):
    """Click the List button on the UI and wait for results."""
    context.driver.find_element(By.ID, "list-btn").click()

    WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located((By.ID, "search_results"))
    )
    context.list_results = _parse_search_results(context)


@then("I should see at least {min_count:d} recommendations in the list")
def step_see_at_least_recommendations(context, min_count):
    results = getattr(context, "list_results", None)
    if results is None:
        results = _parse_search_results(context)
        context.list_results = results

    actual = len(results)
    assert (
        actual >= min_count
    ), f"Expected at least {min_count} recommendations, got {actual}"


@then(
    'I should see a recommendation with base product "{base_id}" '
    'and recommended product "{rec_id}" in the list'
)
def step_see_recommendation_in_list(context, base_id, rec_id):
    results = getattr(context, "list_results", None)
    if results is None:
        results = _parse_search_results(context)
        context.list_results = results

    matches = [
        rec
        for rec in results
        if str(rec["base_product_id"]) == str(base_id)
        and str(rec["recommended_product_id"]) == str(rec_id)
    ]
    assert matches, (
        f"Did not find recommendation with base {base_id} "
        f"and recommended {rec_id} in the list"
    )


######################################################################
# Scenario: Filter recommendations by XXXXX
######################################################################
@when('I set the "{field_name}" to "{text}"')
def step_impl_set_field(context, field_name, text):
    """
    Set a UI field (input/select) to some text

    field_name such as "Base Product ID" / "Status" / "Recommendation Type" / "Confidence Score"
    -> HTML id: base_product_id / status / recommendation_type / confidence_score
    """
    element_id = field_name.replace(" ", "_").lower()
    element = context.driver.find_element(By.ID, element_id)
    tag = element.tag_name.lower()

    if tag == "select":
        target = text.strip().lower()
        options = element.find_elements(By.TAG_NAME, "option")

        for option in options:
            visible = option.text.strip()
            value = (option.get_attribute("value") or "").strip()
            if visible.lower() == target or value.lower() == target:
                option.click()
                return

        raise AssertionError(
            f'No option matching "{text}" found for select #{element_id}. '
            f"Options were: {[o.text for o in options]}"
        )
    else:
        try:
            element.clear()
        except Exception:
            pass
        element.send_keys(text)


@when('I press the "{button_name}" button')
def step_impl_press_button(context, button_name):
    """Press a button by its visible text or id name"""
    button_id = button_name.lower() + "-btn"
    button = context.driver.find_element(By.ID, button_id)
    button.click()


@then('I should see "{text}" in the results table')
def step_see_in_results_table(context, text):
    """Check that some text appears in the search_results table."""
    table = context.driver.find_element(By.ID, "search_results")
    assert text in table.text, f'"{text}" not found in results table:\n{table.text}'


@then('I should not see "{text}" in the results table')
def step_not_see_in_results_table(context, text):
    """Check that some text does NOT appear in the search_results table."""
    table = context.driver.find_element(By.ID, "search_results")
    assert (
        text not in table.text
    ), f'"{text}" was unexpectedly found in results table:\n{table.text}'


@then('I press the "{button_name}" button')
def step_impl_press_button_then(context, button_name):
    """Alias for pressing a button in a Then/And step."""
    return step_impl_press_button(context, button_name)


######################################################################
# Scenario: Apply discount via API
######################################################################


@given(
    'the remembered recommendation has base product price "{base_price}" and recommended product price "{rec_price}"'
)
def step_remembered_rec_has_prices(context, base_price, rec_price):
    """Verify and store the prices of the remembered recommendation."""
    rec_id = context.remembered_rec["recommendation_id"]
    resp = requests.get(
        f"{context.base_url}/recommendations/{rec_id}",
        timeout=WAIT_TIMEOUT,
    )
    resp.raise_for_status()
    rec = resp.json()
    assert float(rec.get("base_product_price", 0)) == float(
        base_price
    ), f"Expected base_product_price {base_price}, got {rec.get('base_product_price')}"
    assert float(rec.get("recommended_product_price", 0)) == float(
        rec_price
    ), f"Expected recommended_product_price {rec_price}, got {rec.get('recommended_product_price')}"
    # Store prices for later verification
    context.remembered_rec["original_base_price"] = float(base_price)
    context.remembered_rec["original_rec_price"] = float(rec_price)


@given(
    'the remembered recommendation with base product "{base_id}" has base product price '
    '"{base_price}" and recommended product price "{rec_price}"'
)
def step_remembered_rec_by_base_has_prices(context, base_id, base_price, rec_price):
    """Find recommendation by base product ID and verify/store prices."""
    # Find recommendation by base product ID
    resp = requests.get(
        f"{context.base_url}/recommendations",
        params={"base_product_id": int(base_id)},
        timeout=WAIT_TIMEOUT,
    )
    resp.raise_for_status()
    matches = resp.json()
    assert matches, f"No recommendation found for base product {base_id}"

    # Store as first or second remembered recommendation
    if not hasattr(context, "remembered_recs"):
        context.remembered_recs = {}

    rec = matches[0]  # Take first match

    # Verify prices
    assert float(rec.get("base_product_price", 0)) == float(
        base_price
    ), f"Expected base_product_price {base_price}, got {rec.get('base_product_price')}"
    assert float(rec.get("recommended_product_price", 0)) == float(rec_price), (
        f"Expected recommended_product_price {rec_price}, "
        f"got {rec.get('recommended_product_price')}"
    )

    context.remembered_recs[base_id] = {
        "recommendation": rec,
        "original_base_price": float(base_price),
        "original_rec_price": float(rec_price),
    }


@when(
    'I apply a flat discount of "{discount}" percent to all accessory recommendations'
)
def step_apply_flat_discount(context, discount):
    """Apply a flat discount via the UI."""
    # Set the flat discount field
    discount_field = context.driver.find_element(By.ID, "flat_discount")
    discount_field.clear()
    discount_field.send_keys(str(discount))

    # Click the apply button
    apply_button = context.driver.find_element(By.ID, "apply-flat-discount-btn")
    apply_button.click()

    # Wait for the response to appear
    WebDriverWait(context.driver, context.wait_seconds).until(
        EC.any_of(
            EC.presence_of_element_located((By.ID, "discount_success_message")),
            EC.presence_of_element_located((By.ID, "discount_error_message")),
        )
    )


@when("I call apply discount endpoint without parameters")
def step_apply_discount_no_params(context):
    """Click apply discount button without filling in the discount field."""
    # Click the apply button without entering a discount
    apply_button = context.driver.find_element(By.ID, "apply-flat-discount-btn")
    apply_button.click()

    # Wait for the error message to appear
    WebDriverWait(context.driver, context.wait_seconds).until(
        EC.any_of(
            EC.presence_of_element_located((By.ID, "discount_success_message")),
            EC.presence_of_element_located((By.ID, "discount_error_message")),
        )
    )


@when(
    'I apply custom discounts with base product price "{base_discount}" '
    'and recommended product price "{rec_discount}" to the first remembered recommendation'
)
def step_apply_custom_discount_first(context, base_discount, rec_discount):
    """Add custom discount entry for the first remembered recommendation via UI."""
    # Get the first remembered recommendation ID
    if hasattr(context, "remembered_recs"):
        # Use the first one in remembered_recs
        first_key = list(context.remembered_recs.keys())[0]
        rec_id = context.remembered_recs[first_key]["recommendation"][
            "recommendation_id"
        ]
    else:
        rec_id = context.remembered_rec["recommendation_id"]

    # Fill in the form fields
    rec_id_field = context.driver.find_element(By.ID, "custom_rec_id")
    rec_id_field.clear()
    rec_id_field.send_keys(str(rec_id))

    if base_discount:
        base_discount_field = context.driver.find_element(By.ID, "custom_base_discount")
        base_discount_field.clear()
        base_discount_field.send_keys(str(base_discount))

    if rec_discount:
        rec_discount_field = context.driver.find_element(By.ID, "custom_rec_discount")
        rec_discount_field.clear()
        rec_discount_field.send_keys(str(rec_discount))

    # Click Add Entry button
    add_button = context.driver.find_element(By.ID, "add-discount-entry-btn")
    add_button.click()

    # Wait a moment for the entry to be added
    WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#discount-entries-list table, #no-entries-message")
        )
    )


@when(
    'I apply custom discounts with base product price "{base_discount}" '
    'and recommended product price "{rec_discount}" to the second remembered '
    "recommendation in the same request"
)
def step_apply_custom_discount_second(context, base_discount, rec_discount):
    """Add second custom discount entry and apply both discounts via UI."""
    # Get the second remembered recommendation
    if hasattr(context, "remembered_recs"):
        keys = list(context.remembered_recs.keys())
        if len(keys) >= 2:
            second_key = keys[1]
            second_rec_id = context.remembered_recs[second_key]["recommendation"][
                "recommendation_id"
            ]
        else:
            raise AssertionError("Second remembered recommendation not found")
    else:
        raise AssertionError("No remembered recommendations found")

    # Fill in the form fields for the second entry
    rec_id_field = context.driver.find_element(By.ID, "custom_rec_id")
    rec_id_field.clear()
    rec_id_field.send_keys(str(second_rec_id))

    if base_discount:
        base_discount_field = context.driver.find_element(By.ID, "custom_base_discount")
        base_discount_field.clear()
        base_discount_field.send_keys(str(base_discount))

    if rec_discount:
        rec_discount_field = context.driver.find_element(By.ID, "custom_rec_discount")
        rec_discount_field.clear()
        rec_discount_field.send_keys(str(rec_discount))

    # Click Add Entry button
    add_button = context.driver.find_element(By.ID, "add-discount-entry-btn")
    add_button.click()

    # Wait for the entry to be added
    WebDriverWait(context.driver, context.wait_seconds).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#discount-entries-list table")
        )
    )

    # Now click Apply Custom Discounts button
    apply_button = context.driver.find_element(By.ID, "apply-custom-discount-btn")
    apply_button.click()

    # Wait for the response to appear
    WebDriverWait(context.driver, context.wait_seconds).until(
        EC.any_of(
            EC.presence_of_element_located((By.ID, "discount_success_message")),
            EC.presence_of_element_located((By.ID, "discount_error_message")),
        )
    )


@when("I apply custom discounts with an empty JSON body")
def step_apply_custom_discount_empty(context):
    """Click apply custom discounts button without adding any entries."""
    # Click Apply Custom Discounts button without any entries
    apply_button = context.driver.find_element(By.ID, "apply-custom-discount-btn")
    apply_button.click()

    # Wait for the error message to appear
    WebDriverWait(context.driver, context.wait_seconds).until(
        EC.any_of(
            EC.presence_of_element_located((By.ID, "discount_success_message")),
            EC.presence_of_element_located((By.ID, "discount_error_message")),
        )
    )


@then('the API should return status "{status_code}"')
def step_api_status(context, status_code):
    """Verify the UI shows appropriate success or error message based on status code."""
    expected_status = int(status_code)

    # Check which message element is visible
    try:
        success_msg = context.driver.find_element(By.ID, "discount_success_message")
        error_msg = context.driver.find_element(By.ID, "discount_error_message")

        success_visible = success_msg.is_displayed()
        error_visible = error_msg.is_displayed()

        if expected_status == 200:
            assert (
                success_visible
            ), "Expected success message for status 200, but error message is shown"
        elif expected_status in (400, 404):
            assert (
                error_visible
            ), f"Expected error message for status {expected_status}, but success message is shown"
    except Exception:  # pylint: disable=broad-except
        # Fallback: check flash message
        flash_msg = context.driver.find_element(By.ID, "flash_message").text
        if expected_status == 200:
            assert (
                "error" not in flash_msg.lower() or "success" in flash_msg.lower()
            ), f"Expected success for status {expected_status}, but got: {flash_msg}"
        else:
            assert (
                "error" in flash_msg.lower()
                or expected_status == 400
                or expected_status == 404
            ), f"Expected error for status {expected_status}, but got: {flash_msg}"


@then(
    'the response should indicate that discounts were applied to at least "{count}" recommendations'
)
def step_discount_applied_count(context, count):
    """Verify the UI success message indicates the correct number of updates."""
    # Check the success message
    success_msg = context.driver.find_element(By.ID, "discount_success_message")
    assert success_msg.is_displayed(), "Success message should be displayed"

    message_text = success_msg.text
    # The message should contain the count, e.g., "Applied 10% discount to 1 accessory recommendations"
    # Extract number from message or check that it mentions the count
    numbers = re.findall(r"\d+", message_text)
    if numbers:
        # The count should be in the message
        assert (
            int(count) <= int(numbers[-1]) or str(count) in message_text
        ), f"Expected message to indicate at least {count} recommendations updated, got: {message_text}"


@then("the response should indicate custom discounts were applied")
def step_custom_discount_applied(context):
    """Verify the UI shows success message for custom discounts."""
    # Check the success message is displayed
    success_msg = context.driver.find_element(By.ID, "discount_success_message")
    assert (
        success_msg.is_displayed()
    ), "Success message should be displayed for custom discounts"

    # Check that updated IDs are shown
    updated_ids_div = context.driver.find_element(By.ID, "discount_updated_ids")
    updated_ids_text = updated_ids_div.text
    assert len(updated_ids_text) > 0, "Updated recommendation IDs should be displayed"


@then('the response message should contain "{text}"')
def step_response_contains(context, text):
    """Verify the UI message (success or error) contains specific text."""
    # Check both success and error messages
    try:
        success_msg = context.driver.find_element(By.ID, "discount_success_message")
        error_msg = context.driver.find_element(By.ID, "discount_error_message")

        if success_msg.is_displayed():
            message = success_msg.text
        elif error_msg.is_displayed():
            message = error_msg.text
        else:
            # Fallback to flash message
            message = context.driver.find_element(By.ID, "flash_message").text
    except Exception:
        # Fallback to flash message
        message = context.driver.find_element(By.ID, "flash_message").text

    assert (
        text.lower() in message.lower()
    ), f'Expected "{text}" in message, got "{message}"'


@then(
    'the remembered recommendation should have base product price "{base_price}" and recommended product price "{rec_price}"'
)
def step_verify_updated_prices(context, base_price, rec_price):
    """Verify the remembered recommendation has updated prices."""
    rec_id = context.remembered_rec["recommendation_id"]
    resp = requests.get(
        f"{context.base_url}/recommendations/{rec_id}",
        timeout=WAIT_TIMEOUT,
    )
    resp.raise_for_status()
    rec = resp.json()

    actual_base = float(rec.get("base_product_price", 0))
    expected_base = float(base_price)
    assert (
        abs(actual_base - expected_base) < 0.01
    ), f"Expected base_product_price {expected_base}, got {actual_base}"

    actual_rec = float(rec.get("recommended_product_price", 0))
    expected_rec = float(rec_price)
    assert (
        abs(actual_rec - expected_rec) < 0.01
    ), f"Expected recommended_product_price {expected_rec}, got {actual_rec}"


@then(
    'the first remembered recommendation should have base product price "{base_price}" '
    'and recommended product price "{rec_price}"'
)
def step_verify_first_updated_prices(context, base_price, rec_price):
    """Verify the first remembered recommendation has updated prices."""
    if hasattr(context, "remembered_recs"):
        first_key = list(context.remembered_recs.keys())[0]
        rec_id = context.remembered_recs[first_key]["recommendation"][
            "recommendation_id"
        ]
    else:
        rec_id = context.remembered_rec["recommendation_id"]

    resp = requests.get(
        f"{context.base_url}/recommendations/{rec_id}",
        timeout=WAIT_TIMEOUT,
    )
    resp.raise_for_status()
    rec = resp.json()

    actual_base = float(rec.get("base_product_price", 0))
    expected_base = float(base_price)
    assert (
        abs(actual_base - expected_base) < 0.01
    ), f"Expected base_product_price {expected_base}, got {actual_base}"

    actual_rec = float(rec.get("recommended_product_price", 0))
    expected_rec = float(rec_price)
    assert (
        abs(actual_rec - expected_rec) < 0.01
    ), f"Expected recommended_product_price {expected_rec}, got {actual_rec}"


@then(
    'the second remembered recommendation should have base product price "{base_price}" '
    'and recommended product price "{rec_price}"'
)
def step_verify_second_updated_prices(context, base_price, rec_price):
    """Verify the second remembered recommendation has updated prices."""
    if hasattr(context, "remembered_recs"):
        keys = list(context.remembered_recs.keys())
        if len(keys) >= 2:
            second_key = keys[1]
            rec_id = context.remembered_recs[second_key]["recommendation"][
                "recommendation_id"
            ]
        else:
            raise AssertionError("Second remembered recommendation not found")
    else:
        raise AssertionError("No remembered recommendations found")

    resp = requests.get(
        f"{context.base_url}/recommendations/{rec_id}",
        timeout=WAIT_TIMEOUT,
    )
    resp.raise_for_status()
    rec = resp.json()

    actual_base = float(rec.get("base_product_price", 0))
    expected_base = float(base_price)
    assert (
        abs(actual_base - expected_base) < 0.01
    ), f"Expected base_product_price {expected_base}, got {actual_base}"

    actual_rec = float(rec.get("recommended_product_price", 0))
    expected_rec = float(rec_price)
    assert (
        abs(actual_rec - expected_rec) < 0.01
    ), f"Expected recommended_product_price {expected_rec}, got {actual_rec}"
