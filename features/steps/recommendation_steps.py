"""Step definitions for recommendation UI feature."""

import requests
from behave import given, when, then  # pylint: disable=no-name-in-module
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from behave import when

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
    """Create the recommendations listed in the Background table."""
    rest_endpoint = f"{context.base_url}/recommendations"
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
        # Accept already-present data (409) to keep Background idempotent
        if resp.status_code not in (HTTP_200_OK, HTTP_201_CREATED, HTTP_409_CONFLICT):
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
    context.remembered_rec = matches[0]


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
# Scenario: Filter recommendations by base_product_id and status via the admin UI
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
