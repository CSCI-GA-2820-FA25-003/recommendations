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
Test cases for Recommendation Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.models import Recommendation, DataValidationError, db
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

    def test_serialize_recommendation(self):
        """It should serialize a Recommendation to dict with correct types"""
        rec = RecommendationFactory()
        rec.create()
        data = rec.serialize()

        # keys exist
        for key in [
            "recommendation_id",
            "base_product_id",
            "recommended_product_id",
            "recommendation_type",
            "status",
            "confidence_score",
            "base_product_price",
            "recommended_product_price",
            "base_product_description",
            "recommended_product_description",
            "created_date",
            "updated_date",
        ]:
            self.assertIn(key, data)

        # type checks
        self.assertIsInstance(data["recommendation_id"], int)
        self.assertIsInstance(data["base_product_id"], int)
        self.assertIsInstance(data["recommended_product_id"], int)
        self.assertIsInstance(data["recommendation_type"], str)
        self.assertIsInstance(data["status"], str)

        # numeric fields serialized to float
        if data["confidence_score"] is not None:
            self.assertIsInstance(data["confidence_score"], float)
            self.assertGreaterEqual(data["confidence_score"], -1.0)
            self.assertLessEqual(data["confidence_score"], 1.0)

        # timestamps
        self.assertTrue(
            data["created_date"].endswith("Z") or "T" in data["created_date"]
        )
        self.assertTrue(
            data["updated_date"].endswith("Z") or "T" in data["updated_date"]
        )

    def test_deserialize_recommendation(self):
        """It should deserialize from a valid dict"""
        payload = {
            "base_product_id": 1001,
            "recommended_product_id": 2002,
            "recommendation_type": "cross-sell",
            "status": "active",
            "confidence_score": "0.75",
            "base_product_price": "19.99",
            "recommended_product_price": "9.50",
            "base_product_description": "Testing: This is a good base product!",
            "recommended_product_description": "Testing: An excellent accessory",
        }
        rec = Recommendation()
        rec.deserialize(payload)

        self.assertEqual(rec.base_product_id, 1001)
        self.assertEqual(rec.recommended_product_id, 2002)
        self.assertEqual(str(rec.recommendation_type), "cross-sell")
        self.assertEqual(str(rec.status), "active")
        self.assertEqual(rec.confidence_score, Recommendation._to_decimal("0.75"))
        self.assertEqual(rec.base_product_price, Recommendation._to_decimal("19.99"))
        self.assertEqual(
            rec.recommended_product_price, Recommendation._to_decimal("9.50")
        )
        self.assertEqual(
            rec.base_product_description, "Testing: This is a good base product!"
        )
        self.assertEqual(
            rec.recommended_product_description, "Testing: An excellent accessory"
        )

    def test_deserialize_missing_required_field(self):
        """It should raise DataValidationError when a required field is missing"""
        payload = {
            # "base_product_id" missing on purpose
            "recommended_product_id": 2002,
            "recommendation_type": "up-sell",
            "status": "inactive",
            "confidence_score": "0.30",
        }
        rec = Recommendation()
        with self.assertRaises(DataValidationError):
            rec.deserialize(payload)

    def test_deserialize_invalid_rec_type(self):
        """It should reject an invalid recommendation_type"""
        payload = {
            "base_product_id": 1,
            "recommended_product_id": 2,
            "recommendation_type": "test",  # not in enum, on purpose
            "status": "active",
            "confidence_score": "0.50",
        }
        rec = Recommendation()
        with self.assertRaises(DataValidationError):
            rec.deserialize(payload)

    def test_deserialize_invalid_status(self):
        """It should reject an invalid status"""
        payload = {
            "base_product_id": 1,
            "recommended_product_id": 2,
            "recommendation_type": "accessory",
            "status": "test",  # not in enum, on purpose
            "confidence_score": "0.50",
        }
        rec = Recommendation()
        with self.assertRaises(DataValidationError):
            rec.deserialize(payload)

    def test_deserialize_confidence_out_of_range_low(self):
        """It should reject confidence_score < -1"""
        payload = {
            "base_product_id": 1,
            "recommended_product_id": 2,
            "recommendation_type": "accessory",
            "status": "active",
            "confidence_score": "-1.01",
        }
        rec = Recommendation()
        with self.assertRaises(DataValidationError):
            rec.deserialize(payload)

    def test_update_recommendation(self):
        """It should update Recommendations"""
        rec = RecommendationFactory(status="active")
        rec.create()
        rec.status = "inactive"
        rec.update()

        fetched = Recommendation.find(rec.id)
        self.assertEqual(str(fetched.status), "inactive")
        # updated_date should be refreshed
        self.assertGreaterEqual(fetched.updated_date, rec.created_date)

    def test_delete_recommendation(self):
        """It should delete a Recommendation"""
        rec1 = RecommendationFactory()
        rec1.create()
        rec2 = RecommendationFactory()
        rec2.create()

        self.assertEqual(len(Recommendation.all()), 2)

        rec1.delete()
        self.assertEqual(len(Recommendation.all()), 1)
        self.assertIsNone(Recommendation.find(rec1.id))

    # def test_find_by_base_product_id(self):
    #     """It should query by base_product_id"""
    #     target_base = 777
    #     r1 = RecommendationFactory(base_product_id=target_base)
    #     r1.create()
    #     r2 = RecommendationFactory(base_product_id=target_base)
    #     r2.create()
    #     r3 = RecommendationFactory(base_product_id=888)
    #     r3.create()

    #     found = Recommendation.find_by_base_product_id(target_base).all()
    #     self.assertEqual(len(found), 2)
    #     self.assertTrue(all(r.base_product_id == target_base for r in found))

    def test_repr(self):
        """It should have a readable __repr__"""
        rec = RecommendationFactory(recommendation_type="up-sell")
        rec.create()
        repr_str = repr(rec)
        self.assertIn("Recommendation id=[", repr_str)
        self.assertIn("type=up-sell", repr_str)
        self.assertIn(f"base={rec.base_product_id}", repr_str)
        self.assertIn(f"rec={rec.recommended_product_id}", repr_str)

    def test_helpers_to_decimal_and_to_float(self):
        """It should convert using _to_decimal/_to_float and keep None"""
        self.assertIsNone(Recommendation._to_decimal(None))
        self.assertIsNone(Recommendation._to_float(None))

        self.assertEqual(
            Recommendation._to_decimal("1.23"), Recommendation._to_decimal(1.23)
        )
        self.assertAlmostEqual(
            Recommendation._to_float(Recommendation._to_decimal("0.90")), 0.90, places=6
        )

    def test_deserialize_type_error_when_none_payload(self):
        """It should raise DataValidationError when payload is None"""
        with self.assertRaises(DataValidationError):
            Recommendation().deserialize(None)

    # Todo: Add your test cases here...
