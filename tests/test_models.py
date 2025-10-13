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
from decimal import Decimal
import os
import logging
from unittest import TestCase
from wsgi import app
from service.models import DataValidationError, Recommendation, db
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

        data = Recommendation.find(recommendation.id)
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

    # Todo: Add your test cases here...
    def test_update_type_normalizes_and_persists(self):
        """It should update a Recommendation's type and normalize it to lowercase"""
        rec = RecommendationFactory(recommendation_type="cross-sell")
        rec.create()
        rec.update({"recommendation_type": "UP-SELL"})
        assert Recommendation.find(rec.id).recommendation_type == "up-sell"

    def test_update_status_normalizes_and_persists(self):
        """It should update a Recommendation's status and normalize it to lowercase"""
        rec = RecommendationFactory(status="inactive")
        rec.create()
        rec.update({"status": "ACTIVE"})
        assert Recommendation.find(rec.id).status == "active"

    def test_update_confidence_valid_and_bounds(self):
        """It should update a Recommendation's confidence_score and ensure it's valid and within bounds [0, 1]"""
        rec = RecommendationFactory(confidence_score="0.4")
        rec.create()
        rec.update({"confidence_score": 0.9})
        assert Recommendation.find(rec.id).confidence_score == Decimal("0.90")

    def test_update_confidence_out_of_range_raises(self):
        """It should raise DataValidationError when updating confidence_score out of range [0, 1]"""
        rec = RecommendationFactory(confidence_score="0.5")
        rec.create()
        with self.assertRaises(DataValidationError):
            rec.update({"confidence_score": 1.2})

    def test_update_fails_for_invalid_status(self):
        """It should raise DataValidationError when updating status to an invalid value"""
        rec = RecommendationFactory(status="active")
        rec.create()
        with self.assertRaises(DataValidationError):
            rec.update({"status": "unknown"})

    def test_update_fails_for_invalid_recommendation_type(self):
        """It should raise DataValidationError when updating recommendation_type to an invalid value"""
        rec = RecommendationFactory(recommendation_type="up-sell")
        rec.create()
        with self.assertRaises(DataValidationError):
            rec.update({"recommendation_type": "invalid-type"})

    def test_update_raises_when_called_without_id(self):
        """Model: update() should raise if the instance has no id (not persisted)."""
        # Build a transient (unsaved) instance with no id
        rec = Recommendation(
            base_product_id=1,
            recommended_product_id=2,
            recommendation_type="cross-sell",
            status="active",
            confidence_score=Decimal("0.50"),
        )
        with self.assertRaises(DataValidationError) as ctx:
            rec.update({})
        self.assertIn("empty ID", str(ctx.exception))

    def test_update_fails_with_invalid_recommendation_type(self):
        """It should raise DataValidationError when updating recommendation_type to an empty value"""
        rec = RecommendationFactory(recommendation_type="up-sell")
        rec.create()
        with self.assertRaises(DataValidationError):
            rec.update({"recommendation_type": ""})

    def test_update_fails_with_invalid_status(self):
        """It should raise DataValidationError when updating status to an empty value"""
        rec = RecommendationFactory(status="active")
        rec.create()
        with self.assertRaises(DataValidationError):
            rec.update({"status": ""})

    def test_update_fails_with_invalid_confidence_score(self):
        """It should raise DataValidationError when updating confidence_score to a non-numeric value"""
        rec = RecommendationFactory(confidence_score="0.5")
        rec.create()
        with self.assertRaises(DataValidationError):
            rec.update({"confidence_score": "not-a-number"})
