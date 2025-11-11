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
BASE_URL = "/recommendations"


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

    def test_index(self):
        """It should return a helpful message"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIn("message", data)
        self.assertIn("Welcome", data["message"])

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
