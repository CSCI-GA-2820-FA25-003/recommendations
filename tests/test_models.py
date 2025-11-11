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
from decimal import Decimal
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.models import (
    DataValidationError,
    ResourceNotFoundError,
    Recommendation,
    db,
)
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

    def test_delete_a_recommendation(self):
        """It should Delete a Recommendation"""
        recommendation = RecommendationFactory()
        recommendation.create()
        self.assertEqual(len(Recommendation.all()), 1)
        # delete the recommendation and make sure it isn't in the database
        recommendation.delete()
        self.assertEqual(len(Recommendation.all()), 0)

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------

    def test_read_a_recommendation(self):
        """It should Read a Recommendation"""
        recommendation = RecommendationFactory()
        logging.debug(recommendation)
        recommendation.id = None
        recommendation.create()
        self.assertIsNotNone(recommendation.id)
        found_recommendation = Recommendation.find(recommendation.id)
        self.assertEqual(found_recommendation.id, recommendation.id)
        self.assertEqual(
            found_recommendation.base_product_id, recommendation.base_product_id
        )
        self.assertEqual(
            found_recommendation.recommended_product_id,
            recommendation.recommended_product_id,
        )
        self.assertEqual(
            found_recommendation.recommendation_type, recommendation.recommendation_type
        )
        self.assertEqual(found_recommendation.status, recommendation.status)
        self.assertEqual(
            found_recommendation.confidence_score, recommendation.confidence_score
        )
        self.assertEqual(
            found_recommendation.base_product_price, recommendation.base_product_price
        )
        self.assertEqual(
            found_recommendation.recommended_product_price,
            recommendation.recommended_product_price,
        )
        self.assertEqual(
            found_recommendation.base_product_description,
            recommendation.base_product_description,
        )
        self.assertEqual(
            found_recommendation.recommended_product_description,
            recommendation.recommended_product_description,
        )
        self.assertEqual(found_recommendation.created_date, recommendation.created_date)
        self.assertEqual(found_recommendation.updated_date, recommendation.updated_date)

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

    # ----------------------------------------------------------
    # Additional Test Cases Added Here
    # ----------------------------------------------------------

    # Test model.py line 62
    def test_repr(self):
        """It should have a readable __repr__"""
        rec = RecommendationFactory(recommendation_type="up-sell")
        rec.create()
        repr_str = repr(rec)
        self.assertIn("Recommendation id=[", repr_str)
        self.assertIn("type=up-sell", repr_str)
        self.assertIn(f"base={rec.base_product_id}", repr_str)
        self.assertIn(f"rec={rec.recommended_product_id}", repr_str)

    # Test model.py line 153, 159
    def test_helpers_to_decimal_and_to_float(self):
        """It should convert using _to_decimal/_to_float"""
        self.assertIsNone(Recommendation._to_decimal(None))
        self.assertIsNone(Recommendation._to_float(None))

        self.assertEqual(
            Recommendation._to_decimal("1.23"), Recommendation._to_decimal(1.23)
        )
        self.assertAlmostEqual(
            Recommendation._to_float(Recommendation._to_decimal("0.90")), 0.90, places=6
        )

    # Test model.py line 229
    def test_deserialize_type_error_when_none_payload(self):
        """It should raise DataValidationError when payload is None"""
        with self.assertRaises(DataValidationError):
            Recommendation().deserialize(None)

    # Test models.py line 225
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

    # ----------------------------------------------------------
    #  Multiple filters
    # ----------------------------------------------------------
    def test_filter_many_status_and_type(self):
        """filter_many: AND status + recommendation_type, case insensitive"""
        a = RecommendationFactory(status="active", recommendation_type="up-sell")
        b = RecommendationFactory(status="active", recommendation_type="cross-sell")
        c = RecommendationFactory(status="inactive", recommendation_type="up-sell")
        a.create()
        b.create()
        c.create()

        q = Recommendation.filter_many(status="ACTIVE", recommendation_type="UP-SELL")
        rows = q.all()
        ids = {r.id for r in rows}
        self.assertEqual(ids, {a.id})

    def test_filter_many_base_status_confidence(self):
        """filter_many: base_product_id + status + min_confidence (>=)"""
        a = RecommendationFactory(
            base_product_id=10, status="active", confidence_score=Decimal("0.50")
        )
        b = RecommendationFactory(
            base_product_id=10, status="active", confidence_score=Decimal("0.90")
        )
        c = RecommendationFactory(
            base_product_id=10, status="inactive", confidence_score=Decimal("0.95")
        )
        d = RecommendationFactory(
            base_product_id=11, status="active", confidence_score=Decimal("0.99")
        )
        a.create()
        b.create()
        c.create()
        d.create()

        q = Recommendation.filter_many(
            base_product_id=10,
            status="ACTIVE",
            min_confidence=0.75,
        )
        rows = q.all()
        ids = {r.id for r in rows}
        # only b meet: base=10 & status=active, confidence>=0.75
        self.assertEqual(ids, {b.id})

    def test_filter_many_min_confidence_inclusive(self):
        """filter_many: min_confidence should >= (inclusive)"""
        r_low = RecommendationFactory(confidence_score=Decimal("0.40"))
        r_eq = RecommendationFactory(confidence_score=Decimal("0.50"))
        r_hi = RecommendationFactory(confidence_score=Decimal("0.90"))
        r_low.create()
        r_eq.create()
        r_hi.create()

        q = Recommendation.filter_many(min_confidence=0.50)
        rows = q.all()
        ids = {r.id for r in rows}
        self.assertIn(r_eq.id, ids)
        self.assertIn(r_hi.id, ids)
        self.assertNotIn(r_low.id, ids)

    def test_filter_many_no_filters_returns_all(self):
        """filter_many: Recommendation.all() if without any filter"""
        a = RecommendationFactory()
        b = RecommendationFactory()
        a.create()
        b.create()
        self.assertCountEqual(
            [r.id for r in Recommendation.filter_many().all()],
            [r.id for r in Recommendation.all()],
        )


######################################################################
#  T E S T   E X C E P T I O N   H A N D L E R S
######################################################################
class TestExceptionHandlers(TestCase):
    """Recommendations Model Exception Handlers"""

    @patch("service.models.db.session.commit")
    def test_create_exception(self, exception_mock):
        """It should catch a create exception"""
        exception_mock.side_effect = Exception()
        recommendation = RecommendationFactory()
        self.assertRaises(DataValidationError, recommendation.create)

    def test_update_exception(self):
        """It should catch an update exception"""
        recommendation = RecommendationFactory(status="active", confidence_score="0.5")
        recommendation.create()

        with patch("service.models.db.session.commit", side_effect=Exception("boom")):
            with self.assertRaises(DataValidationError):
                recommendation.update({"status": "active"})

    @patch("service.models.db.session.commit")
    def test_delete_exception(self, exception_mock):
        """It should catch a delete exception"""
        exception_mock.side_effect = Exception()
        recommendation = RecommendationFactory()
        self.assertRaises(DataValidationError, recommendation.delete)

    def test_apply_custom_discounts_database_error(self):
        """It should wrap database commit errors in DataValidationError"""
        r = RecommendationFactory(
            base_product_price=Decimal("100.00"),
            recommended_product_price=Decimal("50.00"),
        )
        r.create()

        mappings = {str(r.id): {"base_product_price": 10}}

        with patch(
            "service.models.db.session.commit",
            side_effect=Exception("boom"),
        ) as mock_commit:
            with self.assertRaises(DataValidationError) as context:
                Recommendation.apply_custom_discounts(mappings)

        self.assertIn("Database error", str(context.exception))
        mock_commit.assert_called()

    def test_apply_flat_discount_to_accessories_success(self):
        """It should apply flat discount to accessories successfully"""
        # Create accessory recommendations
        Recommendation.query.delete()
        db.session.commit()
        a1 = RecommendationFactory(
            recommendation_type="accessory",
            base_product_price=Decimal("100.00"),
            recommended_product_price=Decimal("50.00"),
        )
        a2 = RecommendationFactory(
            recommendation_type="accessory",
            base_product_price=Decimal("200.00"),
            recommended_product_price=Decimal("25.00"),
        )
        a1.create()
        a2.create()

        updated_ids, count = Recommendation.apply_flat_discount_to_accessories(
            Decimal("10")
        )

        self.assertEqual(count, 2)
        self.assertEqual(set(updated_ids), {a1.id, a2.id})

        # Verify prices were updated
        got_a1 = Recommendation.find(a1.id)
        got_a2 = Recommendation.find(a2.id)
        self.assertEqual(got_a1.base_product_price, Decimal("90.00"))
        self.assertEqual(got_a1.recommended_product_price, Decimal("45.00"))
        self.assertEqual(got_a2.base_product_price, Decimal("180.00"))
        self.assertEqual(got_a2.recommended_product_price, Decimal("22.50"))

    def test_apply_flat_discount_to_accessories_invalid_discount(self):
        """It should raise DataValidationError for invalid discount percentage"""
        with self.assertRaises(DataValidationError) as context:
            Recommendation.apply_flat_discount_to_accessories(Decimal("0"))
        self.assertIn("Discount must be between 0 and 100", str(context.exception))

        with self.assertRaises(DataValidationError) as context:
            Recommendation.apply_flat_discount_to_accessories(Decimal("100"))
        self.assertIn("Discount must be between 0 and 100", str(context.exception))

    def test_apply_custom_discounts_success(self):
        """It should apply custom discounts successfully"""
        r1 = RecommendationFactory(
            base_product_price=Decimal("100.00"),
            recommended_product_price=Decimal("50.00"),
        )
        r2 = RecommendationFactory(
            base_product_price=Decimal("200.00"),
            recommended_product_price=Decimal("25.00"),
        )
        r1.create()
        r2.create()

        discount_mappings = {
            str(r1.id): {"base_product_price": 10, "recommended_product_price": 20},
            str(r2.id): {"base_product_price": 15},
        }

        updated_ids = Recommendation.apply_custom_discounts(discount_mappings)

        self.assertEqual(set(updated_ids), {r1.id, r2.id})

        # Verify prices were updated
        got_r1 = Recommendation.find(r1.id)
        got_r2 = Recommendation.find(r2.id)
        self.assertEqual(got_r1.base_product_price, Decimal("90.00"))  # 10% off
        self.assertEqual(got_r1.recommended_product_price, Decimal("40.00"))  # 20% off
        self.assertEqual(got_r2.base_product_price, Decimal("170.00"))  # 15% off
        self.assertEqual(
            got_r2.recommended_product_price, Decimal("25.00")
        )  # unchanged

    def test_apply_custom_discounts_invalid_mappings(self):
        """It should raise DataValidationError for invalid discount mappings"""
        with self.assertRaises(DataValidationError) as context:
            Recommendation.apply_custom_discounts({})
        self.assertIn(
            "JSON body must map recommendation_id to discount objects",
            str(context.exception),
        )

        with self.assertRaises(DataValidationError) as context:
            Recommendation.apply_custom_discounts("invalid")
        self.assertIn(
            "JSON body must map recommendation_id to discount objects",
            str(context.exception),
        )

    def test_apply_custom_discounts_invalid_recommendation_id_keys(self):
        """It should raise DataValidationError for non-numeric recommendation ID keys"""
        with self.assertRaises(DataValidationError) as context:
            Recommendation.apply_custom_discounts(
                {"invalid": {"base_product_price": 10}}
            )
        self.assertIn("Keys must be numeric recommendation IDs", str(context.exception))

    def test_apply_custom_discounts_invalid_discount_config(self):
        """It should raise DataValidationError for invalid discount configuration"""
        r = RecommendationFactory()
        r.create()

        with self.assertRaises(DataValidationError) as context:
            Recommendation.apply_custom_discounts({str(r.id): "invalid"})
        self.assertIn(
            "Each value must be an object with price discount fields",
            str(context.exception),
        )

        with self.assertRaises(DataValidationError) as context:
            Recommendation.apply_custom_discounts({str(r.id): {}})
        self.assertIn(
            "Each value must be an object with price discount fields",
            str(context.exception),
        )

    def test_apply_custom_discounts_no_discount_fields(self):
        """It should raise DataValidationError when no discount fields are provided"""
        r = RecommendationFactory()
        r.create()

        with self.assertRaises(DataValidationError) as context:
            Recommendation.apply_custom_discounts({str(r.id): {"invalid_field": 10}})
        self.assertIn(
            "Provide at least one of base_product_price or recommended_product_price",
            str(context.exception),
        )

    def test_apply_custom_discounts_invalid_discount_percentages(self):
        """It should raise DataValidationError for invalid discount percentages"""
        r = RecommendationFactory()
        r.create()

        with self.assertRaises(DataValidationError) as context:
            Recommendation.apply_custom_discounts(
                {str(r.id): {"base_product_price": 0}}
            )
        self.assertIn("Discount must be between 0 and 100", str(context.exception))

        with self.assertRaises(DataValidationError) as context:
            Recommendation.apply_custom_discounts(
                {str(r.id): {"base_product_price": 100}}
            )
        self.assertIn("Discount must be between 0 and 100", str(context.exception))

    def test_apply_custom_discounts_nonexistent_recommendation_ids(self):
        """It should skip non-existent recommendation IDs"""
        discount_mappings = {
            "99999": {"base_product_price": 10},  # Non-existent ID
            "99998": {"recommended_product_price": 20},  # Non-existent ID
        }

        updated_ids = Recommendation.apply_custom_discounts(discount_mappings)
        self.assertEqual(updated_ids, [])  # No updates since IDs don't exist

    def test_apply_custom_discounts_with_null_prices(self):
        """It should handle recommendations with null prices correctly"""
        r1 = RecommendationFactory(
            base_product_price=None, recommended_product_price=Decimal("50.00")
        )
        r2 = RecommendationFactory(
            base_product_price=Decimal("100.00"), recommended_product_price=None
        )
        r1.create()
        r2.create()

        discount_mappings = {
            str(r1.id): {
                "base_product_price": 20
            },  # Should be skipped (base_price is null)
            str(r2.id): {
                "recommended_product_price": 30
            },  # Should be skipped (rec_price is null)
        }

        updated_ids = Recommendation.apply_custom_discounts(discount_mappings)
        self.assertEqual(updated_ids, [])  # No updates since prices are null

    ######################################################################
    #  H E L P E R   M E T H O D S   F O R   D I S C O U N T S
    ######################################################################

    def test_validate_discount_percentage_valid_values(self):
        """_validate_discount_percentage: should accept values strictly between 0 and 100"""
        pct = Recommendation._validate_discount_percentage(10)  # type: ignore[attr-defined]
        self.assertEqual(pct, Decimal("10"))

        pct = Recommendation._validate_discount_percentage("25.5")  # type: ignore[attr-defined]
        self.assertEqual(pct, Decimal("25.5"))

    def test_validate_discount_percentage_invalid_type_or_range(self):
        """_validate_discount_percentage: should raise DataValidationError on bad input"""
        # non-numeric
        with self.assertRaises(DataValidationError) as ctx:
            Recommendation._validate_discount_percentage("abc")  # type: ignore[attr-defined]
        self.assertIn("Discount must be between 0 and 100", str(ctx.exception))

        # zero
        with self.assertRaises(DataValidationError):
            Recommendation._validate_discount_percentage(0)  # type: ignore[attr-defined]

        # negative
        with self.assertRaises(DataValidationError):
            Recommendation._validate_discount_percentage(-5)  # type: ignore[attr-defined]

        # >= 100
        with self.assertRaises(DataValidationError):
            Recommendation._validate_discount_percentage(100)  # type: ignore[attr-defined]

    def test_apply_discount_helper_calculates_and_rounds(self):
        """_apply_discount: should compute correct discounted price with 2-decimal rounding"""
        value = Decimal("100.00")
        percent = Decimal("7.5")  # 7.5% off -> 92.50

        discounted = Recommendation._apply_discount(value, percent)  # type: ignore[attr-defined]
        self.assertEqual(discounted, Decimal("92.50"))

        # check rounding behavior (e.g., 1/3 with 10% off)
        value = Decimal("10.005")
        percent = Decimal("0.5")  # 0.5% off
        discounted = Recommendation._apply_discount(value, percent)  # type: ignore[attr-defined]
        # 10.005 * 0.995 = 9.954975 -> 9.95 with ROUND_HALF_UP
        self.assertEqual(discounted, Decimal("9.95"))

    ######################################################################
    #  A P P L Y   F L A T   D I S C O U N T   (M O D E L)
    ######################################################################

    def test_apply_flat_discount_to_accessories_no_accessories(self):
        """apply_flat_discount_to_accessories: should raise ResourceNotFoundError when no accessories"""
        # ensure table empty or only non-accessory rows
        db.session.query(Recommendation).delete()
        db.session.commit()

        non_acc = RecommendationFactory(recommendation_type="cross-sell")
        non_acc.create()

        with self.assertRaises(ResourceNotFoundError) as ctx:
            Recommendation.apply_flat_discount_to_accessories(Decimal("10"))
        self.assertIn("No matching accessory recommendations found", str(ctx.exception))

    def test_apply_flat_discount_to_accessories_only_null_prices(self):
        """apply_flat_discount_to_accessories: should raise ResourceNotFoundError when all prices are null"""
        db.session.query(Recommendation).delete()
        db.session.commit()

        acc1 = RecommendationFactory(
            recommendation_type="accessory",
            base_product_price=None,
            recommended_product_price=None,
        )
        acc1.create()

        with self.assertRaises(ResourceNotFoundError) as ctx:
            Recommendation.apply_flat_discount_to_accessories(Decimal("10"))
        self.assertIn("No matching accessory recommendations found", str(ctx.exception))
