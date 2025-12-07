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
Recommendation Service with Swagger (Flask-RESTX)

This service implements a REST API that allows users to Create, Read, Update
and Delete Recommendations, as well as apply discounts.

UI Routes (no /api prefix):
---------------------------
GET /      - Root JSON
GET /ui    - Static UI page
GET /health - Health check

REST API Routes (all prefixed with /api):
----------------------------------------
GET    /api/recommendations
POST   /api/recommendations
GET    /api/recommendations/<int:recommendation_id>
PUT    /api/recommendations/<int:recommendation_id>
DELETE /api/recommendations/<int:recommendation_id>

PUT    /api/recommendations/apply_discount
"""
from decimal import Decimal, InvalidOperation

from flask import jsonify, request, abort, url_for
from flask import current_app as app  # Import Flask application
from flask_restx import Api, Resource, fields, reqparse, inputs

from service.common import status  # HTTP Status Codes
from service.models import (
    DataValidationError,
    ResourceNotFoundError,
    Recommendation,
)

######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Recommendation REST API Service",
    description="This is a Recommendation service",
    default="recommendations",
    default_label="Recommendation operations",
    doc="/apidocs",  # Swagger UI
    prefix="/api",
)


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for Root URL")
    return (
        jsonify(
            name="Recommendation REST API Service",
            version="1.0",
            message="Welcome to the Recommendation Service! See docs at /apidocs.",
            docs="/apidocs",
            list_url="/recommendations",
        ),
        status.HTTP_200_OK,
    )


######################################################################
# SERVE STATIC UI
######################################################################
@app.route("/ui")
def serve_ui():
    """Serves the static admin UI page"""
    return app.send_static_file("index.html")


######################################################################
#  HEALTH  E N D P O I N T S
######################################################################
@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Kubernetes probes"""
    app.logger.info("Health check requested")
    return jsonify(status="OK"), status.HTTP_200_OK


######################################################################
# Swagger Models & Query Parameters
######################################################################
create_model = api.model(
    "Recommendation",
    {
        "base_product_id": fields.Integer(
            required=True, description="The base product id"
        ),
        "recommended_product_id": fields.Integer(
            required=True, description="The recommended product id"
        ),
        "recommendation_type": fields.String(
            required=False,
            description="Type of recommendation (e.g., cross-sell, up-sell, accessory)",
        ),
        "status": fields.String(
            required=False, description="Status of recommendation (active/inactive)"
        ),
        "confidence_score": fields.Float(
            required=False,
            description="Confidence score between 0 and 1",
        ),
        # Price fields
        "base_product_price": fields.Float(
            required=False, description="Base product price"
        ),
        "recommended_product_price": fields.Float(
            required=False, description="Recommended product price"
        ),
    },
)

recommendation_model = api.inherit(
    "RecommendationModel",
    create_model,
    {
        "id": fields.Integer(
            readOnly=True, description="The unique id assigned to this recommendation"
        ),
    },
)

# List /search's query string parameters
rec_args = reqparse.RequestParser()
rec_args.add_argument(
    "base_product_id",
    type=int,
    location="args",
    required=False,
    help="Filter by base product id",
)
rec_args.add_argument(
    "recommendation_type",
    type=str,
    location="args",
    required=False,
    help="Filter by recommendation type (cross-sell, up-sell, accessory)",
)
rec_args.add_argument(
    "status",
    type=str,
    location="args",
    required=False,
    help="Filter by status (active, inactive)",
)
rec_args.add_argument(
    "confidence_score",
    type=inputs.float,
    location="args",
    required=False,
    help="Filter by minimum confidence score (0..1)",
)

######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
#  PATH: /recommendations/{id}
######################################################################
@api.route("/recommendations/<int:recommendation_id>")
@api.param("recommendation_id", "The Recommendation identifier")
class RecommendationResource(Resource):
    """
    RecommendationResource

    Handles a single Recommendation:
    GET    /recommendations/<id>
    PUT    /recommendations/<id>
    DELETE /recommendations/<id>
    """

    # ------------------------------------------------------------------
    # READ A Recommendation
    # ------------------------------------------------------------------
    @api.doc("get_recommendation")
    @api.response(404, "Recommendation not found")
    @api.marshal_with(recommendation_model)
    def get(self, recommendation_id: int):
        """
        Retrieve a single Recommendation by id
        """
        app.logger.info(
            "Request to Retrieve a Recommendation with id [%s]", recommendation_id
        )
        recommendation = Recommendation.find(recommendation_id)
        if not recommendation:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Recommendation with id '{recommendation_id}' was not found.",
            )

        app.logger.info("Returning recommendation: %s", recommendation.id)
        return recommendation.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE AN EXISTING RECOMMENDATION
    # ------------------------------------------------------------------
    @api.doc("update_recommendation")
    @api.response(404, "Recommendation not found")
    @api.response(400, "The posted Recommendation data was not valid")
    @api.expect(create_model)
    @api.marshal_with(recommendation_model)
    def put(self, recommendation_id: int):
        """
        Update an existing Recommendation's editable fields.

        Request Body (application/json) – at least one field:
            recommendation_type: "up-sell" | "cross-sell" | "accessory"
            confidence_score: 0.0..1.0
            status: "active" | "inactive"
            (and any other editable fields defined in the model)
        """
        app.logger.info(
            "Request to Update recommendation with id: %s", recommendation_id
        )
        check_content_type("application/json")
        rec = Recommendation.find(recommendation_id)
        if rec is None:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Recommendation with id '{recommendation_id}' was not found.",
            )

        data = api.payload or {}
        if not data:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "At least one field is required to update",
            )

        try:
            # Model handles normalization + validation
            rec.update(data)
        except DataValidationError as error:
            abort(status.HTTP_400_BAD_REQUEST, str(error))

        return rec.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE A RECOMMENDATION
    # ------------------------------------------------------------------
    @api.doc("delete_recommendation")
    @api.response(204, "Recommendation deleted")
    def delete(self, recommendation_id: int):
        """
        Delete a Recommendation by id
        """
        app.logger.info(
            "Request to Delete a recommendation with id [%s]", recommendation_id
        )

        recommendation = Recommendation.find(recommendation_id)
        if recommendation:
            app.logger.info("Recommendation with ID: %d found.", recommendation.id)
            recommendation.delete()

        app.logger.info(
            "Recommendation with ID: %d delete complete.", recommendation_id
        )
        return "", status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /recommendations
######################################################################
@api.route("/recommendations", strict_slashes=False)
class RecommendationCollection(Resource):
    """Handles all interactions with collections of Recommendations"""

    # ------------------------------------------------------------------
    # LIST RECOMMENDATIONS - Multiple Filters
    # ------------------------------------------------------------------
    @api.doc("list_recommendations")
    @api.expect(rec_args, validate=True)
    @api.marshal_list_with(recommendation_model)
    def get(self):
        """
        Returns a list of Recommendations.

        Supported query params (all optional, can be combined):
          - base_product_id: int
          - recommendation_type: "cross-sell", "up-sell", "accessory"
          - status: "active", "inactive"
          - confidence_score: float in [0, 1] (minimum threshold, inclusive)
        """
        app.logger.info("Request for recommendation list")

        args = rec_args.parse_args()
        base_product_id = args.get("base_product_id")
        recommendation_type = args.get("recommendation_type")
        rec_status = args.get("status")
        confidence_score = args.get("confidence_score")

        # Validate confidence_score range if provided
        if confidence_score is not None:
            if confidence_score < 0 or confidence_score > 1:
                abort(
                    status.HTTP_400_BAD_REQUEST,
                    "confidence_score must be in [0, 1]",
                )

        # If no filters at all, return all
        if (
            base_product_id is None
            and not recommendation_type
            and not rec_status
            and confidence_score is None
        ):
            app.logger.info("Find all recommendations")
            recs = Recommendation.all()
            results = [r.serialize() for r in recs]
            app.logger.info("Returning %d recommendations", len(results))
            return results, status.HTTP_200_OK

        # Combined filters (logical AND)
        query = Recommendation.filter_many(
            base_product_id=base_product_id,
            recommendation_type=recommendation_type,
            status=rec_status,
            min_confidence=confidence_score,
        )
        rows = query.all()
        results = [r.serialize() for r in rows]
        app.logger.info("Returning %d recommendations", len(results))
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # CREATE A NEW RECOMMENDATION
    # ------------------------------------------------------------------
    @api.doc("create_recommendation")
    @api.response(400, "The posted data was not valid")
    @api.expect(create_model)
    @api.marshal_with(recommendation_model, code=201)
    def post(self):
        """
        Create a Recommendation
        This endpoint will create a Recommendation based on the posted data.
        """
        app.logger.info("Request to Create a Recommendation...")
        check_content_type("application/json")

        recommendation = Recommendation()
        data = api.payload or {}
        app.logger.info("Processing: %s", data)
        try:
            recommendation.deserialize(data)
        except DataValidationError as error:
            abort(status.HTTP_400_BAD_REQUEST, str(error))

        # Save the new Recommendation to the database
        recommendation.create()
        app.logger.info("Recommendation with new id [%s] saved!", recommendation.id)

        # Location header for newly created resource
        location_url = api.url_for(
            RecommendationResource, recommendation_id=recommendation.id, _external=True
        )

        return (
            recommendation.serialize(),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


######################################################################
#  PATH: /recommendations/apply_discount (NON-CRUD ACTION)
######################################################################
@api.route("/recommendations/apply_discount")
class DiscountResource(Resource):
    """Apply discounts to recommendations"""

    @api.doc("apply_discount")
    @api.response(200, "Discounts applied")
    @api.response(400, "Invalid discount payload")
    @api.response(404, "Some recommendations not found")
    def put(self):
        """
        Apply discounts to recommendation prices.

        Modes:
          1) Flat mode (query string):
             PUT /recommendations/apply_discount?discount=10
             - Applies the same percentage to all accessory recommendations.
             - Only updates price fields that are non-null.

          2) Custom mode (JSON body):
             PUT /recommendations/apply_discount
             Content-Type: application/json
             {
               "<recommendation_id>": {
                 "base_product_price": <0..100>,
                 "recommended_product_price": <0..100>
               },
               ...
             }
        """
        app.logger.info("Request to apply discounts")

        # Determine mode
        discount_query_param = request.args.get("discount", type=str)
        request_body = None
        if discount_query_param is None:
            # If no query param, try JSON body for custom mode
            if request.headers.get("Content-Type") and request.data:
                check_content_type("application/json")
            request_body = request.get_json(silent=True)

        # If neither provided -> 400
        if discount_query_param is None and request_body is None:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "At least a query 'discount' or JSON body is required",
            )

        try:
            # Flat mode
            if discount_query_param is not None:
                discount_percentage = validate_discount_percent(discount_query_param)
                (
                    updated_recommendation_ids,
                    updated_count,
                ) = Recommendation.apply_flat_discount_to_accessories(
                    discount_percentage
                )
                return (
                    {
                        "message": (
                            f"Applied {discount_percentage}% discount "
                            f"to {updated_count} accessory recommendations"
                        ),
                        "updated_count": updated_count,
                        "updated_ids": updated_recommendation_ids,
                    },
                    status.HTTP_200_OK,
                )

            # Custom mode
            if not isinstance(request_body, dict) or not request_body:
                abort(
                    status.HTTP_400_BAD_REQUEST,
                    "JSON body must map recommendation_id to discount objects",
                )

            updated_recommendation_ids = Recommendation.apply_custom_discounts(
                request_body
            )
            return (
                {
                    "message": "Applied custom discounts",
                    "updated_ids": updated_recommendation_ids,
                },
                status.HTTP_200_OK,
            )

        except DataValidationError as err:
            abort(status.HTTP_400_BAD_REQUEST, str(err))
        except ResourceNotFoundError as err:
            abort(status.HTTP_404_NOT_FOUND, str(err))


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def abort(error_code: int, message: str):
    """Logs errors before aborting via Flask-RESTX"""
    app.logger.error(message)
    api.abort(error_code, message)


######################################################################
# Discount validation helper
######################################################################
def validate_discount_percent(value) -> Decimal:
    """Validates that discount percentage is between 0 and 100 (exclusive)"""
    try:
        pct = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        abort(status.HTTP_400_BAD_REQUEST, "Discount must be between 0 and 100")

    if pct <= Decimal("0") or pct >= Decimal("100"):
        abort(status.HTTP_400_BAD_REQUEST, "Discount must be between 0 and 100")
    return pct


######################################################################
# Checks the ContentType of a request
######################################################################
def check_content_type(content_type) -> None:
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )
