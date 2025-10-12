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
Test cases for Pet Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.models import Recommendation, db
from .factories import RecommendationFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  Recommendation   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestRecommendation(TestCase):
    """Test Cases for Recommendation Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Recommendation).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_recommendation(self):
        """It should create a Recommendation"""
        recommendation = RecommendationFactory()
        recommendation.create()

        self.assertIsNotNone(recommendation.id)

        found = Recommendation.all()
        self.assertEqual(len(found), 1)

        # TODO: Uncomment the below block once the find()/read() method is restored
        """ data = Recommendation.find(recommendation.id)
        self.assertEqual(data.base_product_id, recommendation.base_product_id)
        self.assertEqual(
            data.recommended_product_id, recommendation.recommended_product_id
        )
        self.assertEqual(data.recommendation_type, recommendation.recommendation_type)
        self.assertEqual(data.status, recommendation.status)
        self.assertEqual(data.confidence_score, recommendation.confidence_score)
        self.assertEqual(data.base_product_price, recommendation.base_product_price)
        self.assertEqual(
            data.recommended_product_price, recommendation.recommended_product_price
        )
        self.assertEqual(
            data.base_product_description, recommendation.base_product_description
        )
        self.assertEqual(
            data.recommended_product_description,
            recommendation.recommended_product_description,
        )
        self.assertEqual(data.created_date, recommendation.created_date)
        self.assertEqual(data.updated_date, recommendation.updated_date)
        """

    def test_all_returns_empty_then_populated(self):
        """It should return [] when empty and all rows when populated"""
        self.assertEqual(len(Recommendation.all()), 0)
        a = RecommendationFactory()
        b = RecommendationFactory()
        a.create()
        b.create()
        rows = Recommendation.all()
        self.assertEqual(len(rows), 2)
        self.assertCountEqual([a.id, b.id], [r.id for r in rows])

    def test_find_by_base_product_id(self):
        """It should filter by base_product_id"""
        r1 = RecommendationFactory(base_product_id=10, recommended_product_id=101)
        r2 = RecommendationFactory(base_product_id=10, recommended_product_id=102)
        r3 = RecommendationFactory(base_product_id=11, recommended_product_id=103)
        r1.create()
        r2.create()
        r3.create()

        q = Recommendation.find_by_base_product_id(10)
        rows = q.all()
        self.assertEqual(len(rows), 2)
        self.assertCountEqual([r1.id, r2.id], [r.id for r in rows])

    def test_find_by_recommendation_type_case_insensitive(self):
        """It should match recommendation_type case-insensitively"""
        r1 = RecommendationFactory(recommendation_type="cross-sell")
        r2 = RecommendationFactory(recommendation_type="up-sell")
        r1.create()
        r2.create()

        q = Recommendation.find_by_recommendation_type("CROSS-SELL")
        rows = q.all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].id, r1.id)

    def test_find_by_status_case_insensitive(self):
        """It should match status case-insensitively"""
        r_active = RecommendationFactory(status="active")
        r_inactive = RecommendationFactory(status="inactive")
        r_active.create()
        r_inactive.create()

        q = Recommendation.find_by_status("ACTIVE")
        rows = q.all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].id, r_active.id)

    def test_find_by_min_confidence_is_inclusive(self):
        """It should include rows with confidence_score >= threshold"""
        r_low = RecommendationFactory(confidence_score="0.40")
        r_eq = RecommendationFactory(confidence_score="0.50")
        r_high = RecommendationFactory(confidence_score="0.90")
        r_low.create()
        r_eq.create()
        r_high.create()

        q = Recommendation.find_by_min_confidence(0.50)
        rows = q.all()
        ids = {r.id for r in rows}
        self.assertIn(r_eq.id, ids)
        self.assertIn(r_high.id, ids)
        self.assertNotIn(r_low.id, ids)

    def test_serialize_contains_expected_fields(self):
        """It should serialize to the expected dict shape/types"""
        rec = RecommendationFactory(
            base_product_id=7,
            recommended_product_id=8,
            recommendation_type="accessory",
            status="active",
            confidence_score="0.65",
            base_product_price="199.99",
            recommended_product_price="19.99",
            base_product_description="Phone",
            recommended_product_description="Case",
        )
        rec.create()

        data = rec.serialize()
        # ids & basics
        self.assertEqual(data["recommendation_id"], rec.id)
        self.assertEqual(data["base_product_id"], 7)
        self.assertEqual(data["recommended_product_id"], 8)
        self.assertEqual(data["recommendation_type"], "accessory")
        self.assertEqual(data["status"], "active")
        # numeric conversions -> float
        self.assertIsInstance(data["confidence_score"], float)
        self.assertAlmostEqual(data["confidence_score"], 0.65, places=6)
        self.assertAlmostEqual(data["base_product_price"], 199.99, places=6)
        self.assertAlmostEqual(data["recommended_product_price"], 19.99, places=6)
        # descriptions
        self.assertEqual(data["base_product_description"], "Phone")
        self.assertEqual(data["recommended_product_description"], "Case")
        # timestamps as ISO strings
        self.assertIsInstance(data["created_date"], str)
        self.assertIsInstance(data["updated_date"], str)
