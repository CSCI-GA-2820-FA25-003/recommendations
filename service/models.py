"""
Models for Recommendation

All of the models are stored in this module
"""

import logging
from datetime import datetime, timezone
from typing import Any, Mapping
from decimal import Decimal, InvalidOperation

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SAEnum

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for data validation errors when deserializing"""


# define Enum
REC_TYPE_ENUM = SAEnum("cross-sell", "up-sell", "accessory", name="rec_type")
STATUS_ENUM = SAEnum("active", "inactive", name="rec_status")

REC_TYPE_VALUES = {"cross-sell", "up-sell", "accessory"}
STATUS_VALUES = {"active", "inactive"}


class Recommendation(db.Model):  # pylint: disable=too-many-instance-attributes
    """
    Class that represents a Recommendation
    """

    __tablename__ = "recommendations"

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column("recommendation_id", db.Integer, primary_key=True)
    base_product_id = db.Column(db.Integer, nullable=False)
    recommended_product_id = db.Column(db.Integer, nullable=False)
    recommendation_type = db.Column(REC_TYPE_ENUM, nullable=False)
    status = db.Column(STATUS_ENUM, nullable=False, default="active")
    confidence_score = db.Column(db.Numeric(3, 2), nullable=False)
    base_product_price = db.Column(db.Numeric(14, 2), nullable=True)
    recommended_product_price = db.Column(db.Numeric(14, 2), nullable=True)
    base_product_description = db.Column(db.String(1023))
    recommended_product_description = db.Column(db.String(1023))
    created_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<Recommendation id=[{self.id}] type={self.recommendation_type} "
            f"base={self.base_product_id} rec={self.recommended_product_id}>"
        )

    def create(self):
        """
        Creates a Recommendation to the database
        """
        logger.info(
            "Creating recommendation %s between product %s and recommended product %s",
            self.id,
            self.base_product_id,
            self.recommended_product_id,
        )
        self.id = None  # pylint: disable=invalid-name
        self.updated_date = datetime.now(timezone.utc)
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record: %s", self)
            raise DataValidationError(e) from e

    # -------------- Helpers for update -------------
    def _require_persisted(self) -> None:
        if not self.id:
            raise DataValidationError("Update called with empty ID field")

    @staticmethod
    def _normalize_required_str(value: Any, field: str) -> str:
        s = str(value).strip().lower()
        if not s:
            raise DataValidationError(f"{field} is required")
        return s

    def _set_enum(self, field: str, value: Any, allowed: set[str]) -> None:
        s = self._normalize_required_str(value, field)
        if s not in allowed:
            raise DataValidationError(f"{field} must be one of {sorted(allowed)}")
        setattr(self, field, s)

    def _set_confidence_score(self, value: Any) -> None:
        try:
            cs = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise DataValidationError("confidence_score must be numeric") from exc
        if cs < Decimal("0") or cs > Decimal("1"):
            raise DataValidationError("confidence_score must be in [0, 1]")
        self.confidence_score = cs

    def _commit_or_raise(self) -> None:
        try:
            db.session.commit()
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            logger.error("Error updating record id=%s: %s", self.id, exc)
            raise DataValidationError(exc) from exc

    def update(self, data: Mapping[str, Any] | None = None) -> None:
        """
        Update this Recommendation (optionally applying partial fields) and commit.
        Allowed updatable fields:
          - recommendation_type  (lowercase enum)
          - status               (lowercase enum)
          - confidence_score     (numeric in [0, 1])
        """
        self._require_persisted()
        if not data:
            return

        handlers = {
            "recommendation_type": lambda v: self._set_enum(
                "recommendation_type", v, REC_TYPE_VALUES
            ),
            "status": lambda v: self._set_enum("status", v, STATUS_VALUES),
            "confidence_score": self._set_confidence_score,
        }

        for key, val in data.items():
            if key not in handlers:
                raise DataValidationError(f"Unknown field: {key}")
            handlers[key](val)

        self.updated_date = datetime.now(timezone.utc)
        self._commit_or_raise()

    def delete(self):
        """Removes a Recommendation from the data store"""
        logger.info(
            "Deleting recommendation %s between base product %s and recommended product %s",
            self.id,
            self.base_product_id,
            self.recommended_product_id,
        )
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    ##################################################
    # Serialize & Deserialize
    ##################################################
    @staticmethod
    def _to_decimal(val):
        if val is None:
            return None
        return Decimal(str(val))

    @staticmethod
    def _to_float(val):
        if val is None:
            return None
        return float(val)

    def serialize(self):
        """Serializes a Recommendation into a dictionary"""
        return {
            "recommendation_id": self.id,
            "base_product_id": self.base_product_id,
            "recommended_product_id": self.recommended_product_id,
            "recommendation_type": (
                str(self.recommendation_type)
                if self.recommendation_type is not None
                else None
            ),
            "status": str(self.status) if self.status is not None else None,
            "confidence_score": self._to_float(self.confidence_score),
            "base_product_price": self._to_float(self.base_product_price),
            "recommended_product_price": self._to_float(self.recommended_product_price),
            "base_product_description": self.base_product_description,
            "recommended_product_description": self.recommended_product_description,
            "created_date": (
                self.created_date.isoformat() if self.created_date else None
            ),
            "updated_date": (
                self.updated_date.isoformat() if self.updated_date else None
            ),
        }

    def deserialize(self, data):
        """
        Deserializes a Recommendation from a dictionary

        Args:
            data (dict): A dictionary containing the recommendation data
        """
        try:
            self.base_product_id = int(data["base_product_id"])
            self.recommended_product_id = int(data["recommended_product_id"])

            rec_type = str(data["recommendation_type"])
            if rec_type not in REC_TYPE_ENUM.enums:
                raise DataValidationError(f"Invalid recommendation_type: {rec_type}")
            self.recommendation_type = rec_type

            status = str(data.get("status", "active"))
            if status not in STATUS_ENUM.enums:
                raise DataValidationError(f"Invalid status: {status}")
            self.status = status

            cs = self._to_decimal(data["confidence_score"])
            if cs < Decimal("0") or cs > Decimal("1"):
                raise DataValidationError("confidence_score must be in [0, 1]")
            self.confidence_score = cs

            self.base_product_price = self._to_decimal(data.get("base_product_price"))
            self.recommended_product_price = self._to_decimal(
                data.get("recommended_product_price")
            )
            self.base_product_description = data.get("base_product_description")
            self.recommended_product_description = data.get(
                "recommended_product_description"
            )

        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Recommendation: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Recommendation: body of request contained bad or no data "
                + str(error)
            ) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all of the Recommendations in the database"""
        logger.info("Processing all Recommendations")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a Recommendation by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.session.get(cls, by_id)

    @classmethod
    def find_by_base_product_id(cls, base_product_id: int):
        """Returns all Recommendations with the given base product id"""
        logger.info("Processing base_product_id query for %s ...", base_product_id)
        return cls.query.filter(cls.base_product_id == base_product_id)

    @classmethod
    def find_by_recommendation_type(cls, rec_type: str):
        """Returns all Recommendations with the given recommendation type"""
        norm = rec_type.strip().lower()
        return cls.query.filter(cls.recommendation_type == norm)

    @classmethod
    def find_by_status(cls, status: str):
        """Returns all Recommendations with the given product availability status"""
        norm = status.strip().lower()
        return cls.query.filter(cls.status == norm)

    @classmethod
    def find_by_min_confidence(cls, threshold: float):
        """Returns all Recommendations with confidence_score >= threshold"""
        logger.info("Processing confidence_score >= %s query ...", threshold)
        return cls.query.filter(cls.confidence_score >= threshold)
