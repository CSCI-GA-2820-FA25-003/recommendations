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

        # Todo: Uncomment this code when get_recommendations in implemented
        # # Check that the location header was correct
        # response = self.client.get(location)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new_recommendation = response.get_json()
        # self.assertEqual(
        #     new_recommendation["base_product_id"], test_recommendation.base_product_id
        # )
        # self.assertEqual(
        #     new_recommendation["recommended_product_id"],
        #     test_recommendation.recommended_product_id,
        # )
        # self.assertEqual(
        #     new_recommendation["recommendation_type"],
        #     test_recommendation.recommendation_type,
        # )
        # self.assertEqual(new_recommendation["status"], test_recommendation.status)
        # self.assertEqual(
        #     new_recommendation["confidence_score"], test_recommendation.confidence_score
        # )
        # self.assertEqual(
        #     new_recommendation["base_product_price"],
        #     test_recommendation.base_product_price,
        # )
        # self.assertEqual(
        #     new_recommendation["recommended_product_price"],
        #     test_recommendation.recommended_product_price,
        # )
        # self.assertEqual(
        #     new_recommendation["base_product_description"],
        #     test_recommendation.base_product_description,
        # )
        # self.assertEqual(
        #     new_recommendation["recommended_product_description"],
        #     test_recommendation.recommended_product_description,
        # )

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
