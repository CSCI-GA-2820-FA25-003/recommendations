"""Step definitions for recommendation UI feature."""

import requests
from behave import given, when, then  # pylint: disable=no-name-in-module
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# HTTP Return Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_409_CONFLICT = 409

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
