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
TestRecommendation API Service Test Suite
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

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

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
