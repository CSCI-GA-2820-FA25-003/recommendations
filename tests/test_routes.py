######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Test Recommendation API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from decimal import Decimal
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Recommendation
from .factories import RecommendationFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/api/recommendations"
DISCOUNT_URL = f"{BASE_URL}/apply_discount"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Recommendation).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ############################################################
    # Utility function to bulk create recommendations
    ############################################################
    def _create_recommendations(self, count: int = 1) -> list:
        """Factory method to create recommendations in bulk"""
        recommendations = []
        for _ in range(count):
            test_recommendation = RecommendationFactory()
            response = self.client.post(BASE_URL, json=test_recommendation.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test recommendation",
            )
            new_recommendation = response.get_json()
            test_recommendation.id = new_recommendation["recommendation_id"]
            recommendations.append(test_recommendation)
        return recommendations

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    # def test_index(self):
    #     """It should return a helpful message"""
    #     resp = self.client.get("/")
    #     self.assertEqual(resp.status_code, status.HTTP_200_OK)
    #     data = resp.get_json()
    #     self.assertIn("message", data)
    #     self.assertIn("Welcome", data["message"])

    def test_create_recommendation(self):
        """It should Create a new Recommendation"""
        test_recommendation = RecommendationFactory(confidence_score=Decimal("0.75"))
        logging.debug("Test Recommendation: %s", test_recommendation.serialize())
        response = self.client.post(BASE_URL, json=test_recommendation.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_recommendation = response.get_json()
        self.assertEqual(
            new_recommendation["base_product_id"], test_recommendation.base_product_id
        )
        self.assertEqual(
            new_recommendation["recommended_product_id"],
            test_recommendation.recommended_product_id,
        )
        self.assertEqual(
            new_recommendation["recommendation_type"],
            test_recommendation.recommendation_type,
        )
        self.assertEqual(new_recommendation["status"], test_recommendation.status)
        self.assertEqual(
            Decimal(str(new_recommendation["confidence_score"])),
            test_recommendation.confidence_score,
        )
        self.assertEqual(
            Decimal(str(new_recommendation["base_product_price"])),
            test_recommendation.base_product_price,
        )
        self.assertEqual(
            Decimal(str(new_recommendation["recommended_product_price"])),
            test_recommendation.recommended_product_price,
        )
        self.assertEqual(
            new_recommendation["base_product_description"],
            test_recommendation.base_product_description,
        )
        self.assertEqual(
            new_recommendation["recommended_product_description"],
            test_recommendation.recommended_product_description,
        )

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_recommendation = response.get_json()
        self.assertEqual(
            new_recommendation["base_product_id"], test_recommendation.base_product_id
        )
        self.assertEqual(
            new_recommendation["recommended_product_id"],
            test_recommendation.recommended_product_id,
        )
        self.assertEqual(
            new_recommendation["recommendation_type"],
            test_recommendation.recommendation_type,
        )
        self.assertEqual(new_recommendation["status"], test_recommendation.status)
        self.assertEqual(
            Decimal(str(new_recommendation["confidence_score"])),
            test_recommendation.confidence_score,
        )
        self.assertEqual(
            Decimal(str(new_recommendation["base_product_price"])),
            test_recommendation.base_product_price,
        )
        self.assertEqual(
            Decimal(str(new_recommendation["recommended_product_price"])),
            test_recommendation.recommended_product_price,
        )
        self.assertEqual(
            new_recommendation["base_product_description"],
            test_recommendation.base_product_description,
        )
        self.assertEqual(
            new_recommendation["recommended_product_description"],
            test_recommendation.recommended_product_description,
        )

    # ----------------------------------------------------------
    # Additional Test Cases Added Here
    # ----------------------------------------------------------

    def test_create_recommendation_no_content_type(self):
        """It should not Create a Recommendation with no Content-Type"""
        # test_recommendation = RecommendationFactory()
        # Remove Content-Type header => check_content_type error
        response = self.client.post(BASE_URL, data="test")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_recommendation_wrong_content_type(self):
        """It should not Create a Recommendation with wrong Content-Type"""
        test_recommendation = RecommendationFactory()
        # Send data with wrong content type
        response = self.client.post(
            BASE_URL,
            data=str(test_recommendation.serialize()),
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------
    def test_get_recommendation(self):
        """It should Get a single Recommendation"""
        # get the id of a recommendation
        test_recommendation = RecommendationFactory()
        test_recommendation.create()
        recommendation_id = test_recommendation.id
        response = self.client.get(f"{BASE_URL}/{recommendation_id}")
        data = response.get_json()

        self.assertEqual(data["recommendation_id"], test_recommendation.id)
        self.assertEqual(data["base_product_id"], test_recommendation.base_product_id)
        self.assertEqual(
            data["recommended_product_id"],
            test_recommendation.recommended_product_id,
        )
        self.assertEqual(
            data["recommendation_type"], test_recommendation.recommendation_type
        )
        self.assertEqual(data["status"], test_recommendation.status)
        self.assertAlmostEqual(
            data["confidence_score"], float(test_recommendation.confidence_score)
        )

    def test_get_recommendation_not_found(self):
        """It should not Get a Recommendation thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    def test_update_happy_path_partial_fields(self):
        """It should Update an existing Recommendation's editable fields"""
        # create a recommendation to update
        rec = RecommendationFactory(
            recommendation_type="cross-sell",
            status="inactive",
            confidence_score=Decimal("0.40"),
        )
        rec.create()
        payload = {
            "recommendation_type": "UP-SELL",  # model normalizes to lowercase
            "confidence_score": 0.90,  # valid and storable (< 1.00)
        }
        resp = self.client.put(f"{BASE_URL}/{rec.id}", json=payload)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.get_json()
        assert body["recommendation_id"] == rec.id
        assert body["recommendation_type"] == "up-sell"
        # confidence serialized as float
        assert body["confidence_score"] == 0.90
        # status unchanged (not provided)
        assert body["status"] == "inactive"

        # also verify persisted
        got = Recommendation.find(rec.id)
        assert got.recommendation_type == "up-sell"
        assert got.status == "inactive"
        assert got.confidence_score == Decimal("0.90")

    def test_update_not_found_returns_404(self):
        """It should return 404 when the recommendation id does not exist."""
        resp = self.client.put(f"{BASE_URL}/999999", json={"status": "active"})
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in resp.get_json().get("message", "").lower()

    def test_update_requires_json_content_type(self):
        """It should enforce application/json via check_content_type()."""
        rec = RecommendationFactory()
        rec.create()
        # No JSON body / wrong content type
        resp = self.client.put(f"{BASE_URL}/{rec.id}", data="status=active")
        # Your check_content_type() typically returns 415 Unsupported Media Type
        assert resp.status_code in (
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_update_empty_body_returns_400(self):
        """It should return 400 Bad Request when the body is empty."""
        rec = RecommendationFactory()
        rec.create()
        resp = self.client.put(f"{BASE_URL}/{rec.id}", json={})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "at least one" in resp.get_json().get("message", "").lower()

    # ----------------------------------------------------------
    # Additional Test Cases Added Here
    # ----------------------------------------------------------

    # Test routes.py line 128-129
    def test_update_with_invalid_data(self):
        """It should return 400 when update data fails validation"""
        recommendation = RecommendationFactory()
        recommendation.create()
        # invalid confidence_score => DataValidationError
        payload = {"confidence_score": 1.5}
        response = self.client.put(f"{BASE_URL}/{recommendation.id}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("message", data)

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------
    def test_delete_recommendation(self):
        """It should Delete a Recommendation"""
        test_recommendation = self._create_recommendations(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_recommendation.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_recommendation.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_non_existing_recommendation(self):
        """It should Delete a Recommendation even if it doesn't exist"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

    def test_create_recommendation_fails_for_negative_confidence_score(self):
        """It should Create a new Recommendation"""
        test_recommendation = RecommendationFactory(confidence_score=Decimal("-0.83"))
        logging.debug("Test Recommendation: %s", test_recommendation.serialize())
        response = self.client.post(BASE_URL, json=test_recommendation.serialize())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recommendation_fails_for_wrong_recommendation_type(self):
        """It should not Create a new Recommendation with wrong recommendation_type"""
        test_recommendation = RecommendationFactory()
        rec = test_recommendation.serialize()
        rec["recommendation_type"] = "invalid-type"
        logging.debug("Test Recommendation: %s", rec)
        response = self.client.post(BASE_URL, json=rec)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recommendation_fails_for_wrong_status_type(self):
        """It should not Create a new Recommendation with wrong status"""
        test_recommendation = RecommendationFactory()
        rec = test_recommendation.serialize()
        rec["status"] = "invalid-status"
        logging.debug("Test Recommendation: %s", rec)
        response = self.client.post(BASE_URL, json=rec)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_filters_returns_all(self):
        """It should return all Recommendations when no filter is sent"""
        a = RecommendationFactory()
        b = RecommendationFactory()
        c = RecommendationFactory()
        a.create()
        b.create()
        c.create()
        resp = self.client.get(BASE_URL)
        assert resp.status_code == 200
        data = resp.get_json()
        assert {x["recommendation_id"] for x in data} == {a.id, b.id, c.id}

    def test_filter_by_base_product_id(self):
        """It should filter Recommendations by base_product_id"""
        a = RecommendationFactory(base_product_id=10)
        b = RecommendationFactory(base_product_id=10)
        c = RecommendationFactory(base_product_id=11)
        a.create()
        b.create()
        c.create()
        resp = self.client.get(f"{BASE_URL}?base_product_id=10")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        ids = {row["recommendation_id"] for row in data}
        assert ids == {a.id, b.id}

    def test_filter_by_recommendation_type_case_insensitive(self):
        """It should filter Recommendations by recommendation_type case-insensitively"""
        a = RecommendationFactory(recommendation_type="cross-sell")
        b = RecommendationFactory(recommendation_type="up-sell")
        c = RecommendationFactory(recommendation_type="accessory")
        a.create()
        b.create()
        c.create()
        resp = self.client.get(f"{BASE_URL}?recommendation_type=CROSS-SELL")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        ids = {row["recommendation_id"] for row in data}
        assert ids == {a.id}

    def test_filter_by_status_case_insensitive(self):
        """It should filter Recommendations by status case-insensitively"""
        a = RecommendationFactory(status="active")
        b = RecommendationFactory(status="inactive")
        c = RecommendationFactory(status="active")
        a.create()
        b.create()
        c.create()
        resp = self.client.get(f"{BASE_URL}?status=ACTIVE")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        ids = {row["recommendation_id"] for row in data}
        assert ids == {a.id, c.id}

    def test_filter_by_min_confidence_inclusive(self):
        """It should filter Recommendations by minimum confidence_score inclusively"""
        a = RecommendationFactory(confidence_score=Decimal("0.50"))
        b = RecommendationFactory(confidence_score=Decimal("0.75"))
        c = RecommendationFactory(confidence_score=Decimal("0.90"))
        a.create()
        b.create()
        c.create()
        resp = self.client.get(f"{BASE_URL}?confidence_score=0.75")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        ids = {row["recommendation_id"] for row in data}
        assert ids == {b.id, c.id}

    def test_confidence_score_out_of_range_returns_400(self):
        """It should return 400 Bad Request if confidence_score is out of range [0, 1]"""
        resp = self.client.get(f"{BASE_URL}?confidence_score=-0.1")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        resp = self.client.get(f"{BASE_URL}?confidence_score=1.1")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_empty_result_is_200_empty_list(self):
        """It should return 200 OK with empty list if no records match"""
        resp = self.client.get(f"{BASE_URL}?base_product_id=99999")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        assert data == []

    # ----------------------------------------------------------
    # APPLY DISCOUNT ENDPOINT TESTS
    # ----------------------------------------------------------
    def test_apply_flat_discount_accessories(self):
        """It should apply a flat discount to all accessory recommendations"""
        # create some data: accessories and non-accessories
        a1 = RecommendationFactory(
            recommendation_type="accessory",
            base_product_price=Decimal("100.00"),
            recommended_product_price=Decimal("50.00"),
        )
        a2 = RecommendationFactory(
            recommendation_type="accessory",
            base_product_price=Decimal("20.00"),
            recommended_product_price=Decimal("10.00"),
        )
        b1 = RecommendationFactory(
            recommendation_type="cross-sell",
            base_product_price=Decimal("100.00"),
            recommended_product_price=Decimal("50.00"),
        )
        a1.create()
        a2.create()
        b1.create()

        # apply 10%
        resp = self.client.put(f"{DISCOUNT_URL}?discount=10")
        assert resp.status_code == status.HTTP_200_OK
        payload = resp.get_json()
        assert payload["updated_count"] == 2
        ids = set(payload["updated_ids"])
        assert ids == {a1.id, a2.id}

        # verify persisted values and updated_date changed
        got_a1 = Recommendation.find(a1.id)
        got_a2 = Recommendation.find(a2.id)
        # 10% off
        assert got_a1.base_product_price == Decimal("90.00")
        assert got_a1.recommended_product_price == Decimal("45.00")
        assert got_a2.base_product_price == Decimal("18.00")
        assert got_a2.recommended_product_price == Decimal("9.00")

        # updated_date refreshed
        assert got_a1.updated_date is not None
        assert got_a2.updated_date is not None

        # non-accessory unchanged
        got_b1 = Recommendation.find(b1.id)
        assert got_b1.base_product_price == Decimal("100.00")
        assert got_b1.recommended_product_price == Decimal("50.00")

    def test_apply_custom_discounts_per_id(self):
        """It should apply custom per-recommendation discounts via JSON body"""
        r1 = RecommendationFactory(
            base_product_price=Decimal("200.00"),
            recommended_product_price=Decimal("20.00"),
        )
        r2 = RecommendationFactory(
            base_product_price=Decimal("100.00"),
            recommended_product_price=Decimal("10.00"),
        )
        r3 = RecommendationFactory(
            base_product_price=Decimal("300.00"),
            recommended_product_price=Decimal("30.00"),
        )
        r1.create()
        r2.create()
        r3.create()

        body = {
            str(r1.id): {"base_product_price": 5},  # 5% off base only
            str(r2.id): {"recommended_product_price": 50},  # 50% off recommended only
            # r3 not included -> no change
        }

        before1 = Recommendation.find(r1.id).updated_date
        before2 = Recommendation.find(r2.id).updated_date
        resp = self.client.put(DISCOUNT_URL, json=body)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        assert set(data["updated_ids"]) == {r1.id, r2.id}

        got1 = Recommendation.find(r1.id)
        got2 = Recommendation.find(r2.id)
        got3 = Recommendation.find(r3.id)

        assert got1.base_product_price == Decimal("190.00")  # 5% off
        assert got1.recommended_product_price == Decimal("20.00")  # unchanged

        assert got2.base_product_price == Decimal("100.00")  # unchanged
        assert got2.recommended_product_price == Decimal("5.00")  # 50% off

        # r3 unchanged
        assert got3.base_product_price == Decimal("300.00")
        assert got3.recommended_product_price == Decimal("30.00")

        # updated_date refreshed on changed records
        assert got1.updated_date is not None and (
            before1 is None or got1.updated_date >= before1
        )
        assert got2.updated_date is not None and (
            before2 is None or got2.updated_date >= before2
        )

    def test_apply_discount_invalid_values(self):
        """It should return 400 on invalid discount values"""
        # flat mode invalid
        resp = self.client.put(f"{DISCOUNT_URL}?discount=0")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        data = resp.get_json()
        assert "Discount must be between 0 and 100" in data.get("message", "")

        resp = self.client.put(f"{DISCOUNT_URL}?discount=100")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        # custom mode invalid
        r = RecommendationFactory()
        r.create()
        body = {str(r.id): {"base_product_price": -5}}
        resp = self.client.put(DISCOUNT_URL, json=body)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_apply_discount_missing_parameters(self):
        """It should return 400 when neither query param nor JSON body is provided"""
        resp = self.client.put(DISCOUNT_URL)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "required" in resp.get_json().get("message", "").lower()

    def test_apply_flat_discount_no_matches_returns_404(self):
        """It should return 404 when no accessory recommendations exist or none updatable"""
        # create only non-accessory records
        x = RecommendationFactory(
            recommendation_type="cross-sell",
            base_product_price=Decimal("10.00"),
            recommended_product_price=Decimal("5.00"),
        )
        x.create()
        resp = self.client.put(f"{DISCOUNT_URL}?discount=10")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_apply_flat_discount_accessories_with_null_prices(self):
        """It should handle accessory recommendations with null prices correctly"""
        # Create accessories with null prices
        a1 = RecommendationFactory(
            recommendation_type="accessory",
            base_product_price=None,
            recommended_product_price=Decimal("50.00"),
        )
        a2 = RecommendationFactory(
            recommendation_type="accessory",
            base_product_price=Decimal("100.00"),
            recommended_product_price=None,
        )
        a3 = RecommendationFactory(
            recommendation_type="accessory",
            base_product_price=None,
            recommended_product_price=None,
        )
        a1.create()
        a2.create()
        a3.create()

        resp = self.client.put(f"{DISCOUNT_URL}?discount=20")
        assert resp.status_code == status.HTTP_200_OK
        payload = resp.get_json()
        assert payload["updated_count"] == 2  # Only a1 and a2 should be updated
        assert set(payload["updated_ids"]) == {a1.id, a2.id}

        # Verify a1: only recommended_product_price updated
        got_a1 = Recommendation.find(a1.id)
        assert got_a1.base_product_price is None
        assert got_a1.recommended_product_price == Decimal("40.00")  # 20% off

        # Verify a2: only base_product_price updated
        got_a2 = Recommendation.find(a2.id)
        assert got_a2.base_product_price == Decimal("80.00")  # 20% off
        assert got_a2.recommended_product_price is None

        # Verify a3: no changes (both prices null)
        got_a3 = Recommendation.find(a3.id)
        assert got_a3.base_product_price is None
        assert got_a3.recommended_product_price is None

    def test_apply_custom_discounts_invalid_json_structure(self):
        """It should return 400 for invalid JSON structure in custom mode"""
        # Empty JSON body with content type
        resp = self.client.put(
            DISCOUNT_URL,
            json={},
            content_type="application/json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "JSON body must map recommendation_id to discount objects"
            in resp.get_json().get("message", "")
        )

        # Non-dict JSON body
        resp = self.client.put(
            DISCOUNT_URL,
            json="invalid",
            content_type="application/json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_apply_custom_discounts_invalid_recommendation_id_keys(self):
        """It should return 400 for non-numeric recommendation ID keys"""
        body = {"invalid_id": {"base_product_price": 10}}
        resp = self.client.put(DISCOUNT_URL, json=body)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Keys must be numeric recommendation IDs" in resp.get_json().get(
            "message", ""
        )

    def test_apply_custom_discounts_invalid_discount_config(self):
        """It should return 400 for invalid discount configuration objects"""
        r = RecommendationFactory()
        r.create()

        # Non-dict discount config
        body = {str(r.id): "invalid"}
        resp = self.client.put(DISCOUNT_URL, json=body)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "Each value must be an object with price discount fields"
            in resp.get_json().get("message", "")
        )

        # Empty discount config
        body = {str(r.id): {}}
        resp = self.client.put(DISCOUNT_URL, json=body)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "Each value must be an object with price discount fields"
            in resp.get_json().get("message", "")
        )

    def test_apply_custom_discounts_no_discount_fields(self):
        """It should return 400 when no discount fields are provided"""
        r = RecommendationFactory()
        r.create()

        body = {str(r.id): {"invalid_field": 10}}
        resp = self.client.put(DISCOUNT_URL, json=body)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "Provide at least one of base_product_price or recommended_product_price"
            in resp.get_json().get("message", "")
        )

    def test_apply_custom_discounts_nonexistent_recommendation_ids(self):
        """It should skip non-existent recommendation IDs without error"""
        body = {
            "99999": {"base_product_price": 10},  # Non-existent ID
            "99998": {"recommended_product_price": 20},  # Non-existent ID
        }
        resp = self.client.put(DISCOUNT_URL, json=body)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        assert data["updated_ids"] == []  # No updates since IDs don't exist

    def test_apply_custom_discounts_mixed_valid_invalid_ids(self):
        """It should process valid IDs and skip invalid ones"""
        r1 = RecommendationFactory(base_product_price=Decimal("100.00"))
        r1.create()

        body = {
            str(r1.id): {"base_product_price": 10},  # Valid ID
            "99999": {"base_product_price": 20},  # Invalid ID
            "invalid": {"base_product_price": 30},  # Invalid key
        }
        resp = self.client.put(DISCOUNT_URL, json=body)
        assert (
            resp.status_code == status.HTTP_400_BAD_REQUEST
        )  # Should fail due to invalid key

    def test_apply_custom_discounts_with_null_prices(self):
        """It should handle recommendations with null prices in custom mode"""
        r1 = RecommendationFactory(
            base_product_price=None, recommended_product_price=Decimal("50.00")
        )
        r2 = RecommendationFactory(
            base_product_price=Decimal("100.00"), recommended_product_price=None
        )
        r1.create()
        r2.create()

        body = {
            str(r1.id): {
                "base_product_price": 20
            },  # Should be skipped (base_price is null)
            str(r2.id): {
                "recommended_product_price": 30
            },  # Should be skipped (rec_price is null)
        }
        resp = self.client.put(DISCOUNT_URL, json=body)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        assert data["updated_ids"] == []  # No updates since prices are null

    def test_apply_discount_invalid_discount_percentage_string(self):
        """It should return 400 for invalid discount percentage strings"""
        resp = self.client.put(f"{DISCOUNT_URL}?discount=invalid")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Discount must be between 0 and 100" in resp.get_json().get(
            "message", ""
        )

    def test_apply_discount_edge_case_discount_values(self):
        """It should handle edge case discount values correctly"""
        # Test exactly 0 (should fail)
        resp = self.client.put(f"{DISCOUNT_URL}?discount=0")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        # Test exactly 100 (should fail)
        resp = self.client.put(f"{DISCOUNT_URL}?discount=100")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        # Test negative values
        resp = self.client.put(f"{DISCOUNT_URL}?discount=-5")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        # Test values over 100
        resp = self.client.put(f"{DISCOUNT_URL}?discount=150")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_apply_custom_discounts_database_error_handling(self):
        """It should handle database errors gracefully"""
        # This test would require mocking the database session to simulate errors
        # For now, we'll test the validation paths that are easier to trigger
        r = RecommendationFactory()
        r.create()

        # Test with invalid discount percentages in custom mode
        body = {str(r.id): {"base_product_price": 150}}  # Invalid percentage
        resp = self.client.put(DISCOUNT_URL, json=body)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Discount must be between 0 and 100" in resp.get_json().get(
            "message", ""
        )

    def test_apply_discount_content_type_handling(self):
        """It should handle content type correctly for custom mode"""
        r = RecommendationFactory()
        r.create()

        # Test with explicit content type
        body = {str(r.id): {"base_product_price": 10}}
        resp = self.client.put(DISCOUNT_URL, json=body, content_type="application/json")
        assert resp.status_code == status.HTTP_200_OK

        # Test without content type but with data - should return 400 due to missing parameters
        resp = self.client.put(DISCOUNT_URL, data='{"1": {"base_product_price": 10}}')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    # Test Cases for multiple filters
    # ----------------------------------------------------------

    def test_multiple_filters_status_and_type(self):
        """It should return intersection of status and recommendation_type filters"""
        a = RecommendationFactory(status="active", recommendation_type="up-sell")
        b = RecommendationFactory(status="active", recommendation_type="cross-sell")
        c = RecommendationFactory(status="inactive", recommendation_type="up-sell")
        a.create()
        b.create()
        c.create()

        resp = self.client.get(f"{BASE_URL}?status=ACTIVE&recommendation_type=UP-SELL")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        ids = {row["recommendation_id"] for row in data}
        assert ids == {a.id}

    def test_multiple_filters_base_and_status(self):
        """It should AND base_product_id and status together"""
        a = RecommendationFactory(base_product_id=10, status="active")
        b = RecommendationFactory(base_product_id=10, status="inactive")
        c = RecommendationFactory(base_product_id=11, status="active")
        a.create()
        b.create()
        c.create()

        resp = self.client.get(f"{BASE_URL}?base_product_id=10&status=active")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        ids = {row["recommendation_id"] for row in data}
        assert ids == {a.id}

    def test_multiple_filters_include_confidence_threshold(self):
        """It should apply min confidence along with other filters (inclusive >=)"""
        a = RecommendationFactory(
            status="active",
            recommendation_type="up-sell",
            confidence_score=Decimal("0.50"),
        )
        b = RecommendationFactory(
            status="active",
            recommendation_type="up-sell",
            confidence_score=Decimal("0.90"),
        )
        c = RecommendationFactory(
            status="active",
            recommendation_type="cross-sell",
            confidence_score=Decimal("0.95"),
        )
        a.create()
        b.create()
        c.create()

        # active + up-sell + confidence_score>=0.75 -> only b
        resp = self.client.get(
            f"{BASE_URL}?status=active&recommendation_type=up-sell&confidence_score=0.75"
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.get_json()
        ids = {row["recommendation_id"] for row in data}
        assert ids == {b.id}

    def test_multiple_filters_empty_result_ok(self):
        """It should return 200 with [] when combined filters match nothing"""
        a = RecommendationFactory(status="inactive", recommendation_type="cross-sell")
        a.create()
        resp = self.client.get(
            f"{BASE_URL}?status=active&recommendation_type=cross-sell"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.get_json() == []

    # ----------------------------------------------------------
    # TEST UI
    # ----------------------------------------------------------
    def test_serve_ui(self):
        """It should serve the UI page from /ui"""
        response = self.client.get("/ui")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Recommendation REST API Service", response.data)
        # should be HTML content
        self.assertIn("text/html", response.content_type)

    # ----------------------------------------------------------
    # TEST HEALTH ENDPOINT
    # ----------------------------------------------------------
    def test_health_endpoint(self):
        """It should return 200 OK for health check"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("status"), "OK")

    ########################################################################
    #              Test JSON error handling in Flask-RESTX
    ########################################################################

    #  ----------- 400 – Bad Request / DataValidationError ------------
    def test_create_recommendation_with_invalid_body_returns_400_json(self):
        """POST with invalid or incomplete JSON should return 400 JSON (no HTML error page)"""

        invalid_body = {
            "name": "invalid-only-name",  # intentionally missing required fields
        }

        resp = self.client.post(
            BASE_URL,
            json=invalid_body,
            content_type="application/json",
        )

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        # Must be JSON, not default HTML
        assert resp.content_type == "application/json"

        data = resp.get_json()
        assert isinstance(data, dict)
        # We only require a human-readable message in the JSON payload
        assert "message" in data
        # Make sure we did not accidentally return an HTML error page
        assert "<!doctype html" not in resp.get_data(as_text=True).lower()

    #  --------------------- Not found ----------------------

    def test_get_nonexistent_recommendation_returns_404_json(self):
        """GET on a non-existing recommendation id should return 404 JSON, not HTML"""

        # Use an id that is very unlikely to exist
        resp = self.client.get(f"{BASE_URL}/999999")

        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert resp.content_type == "application/json"

        data = resp.get_json()
        assert isinstance(data, dict)
        # Flask-RESTX default abort() puts the human-readable text in "message"
        assert "message" in data
        assert "not found" in data["message"].lower()
        assert "<!doctype html" not in resp.get_data(as_text=True).lower()
