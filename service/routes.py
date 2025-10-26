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
Recommendation Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Recommendation
"""

from flask import jsonify, request, abort, url_for
from flask import current_app as app  # Import Flask application
from service.models import DataValidationError, Recommendation
from service.common import status  # HTTP Status Codes


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
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
# CREATE A NEW RECOMMENDATION
######################################################################
@app.route("/recommendations", methods=["POST"])
def create_recommendations():
    """
    Create a Recommendation
    This endpoint will create a Recommendation based the data in the body that is posted
    """
    app.logger.info("Request to Create a Recommendation...")
    check_content_type("application/json")

    recommendation = Recommendation()
    # Get the data from the request and deserialize it
    data = request.get_json()
    app.logger.info("Processing: %s", data)
    recommendation.deserialize(data)

    # Save the new Recommendation to the database
    recommendation.create()
    app.logger.info("Recommendation with new id [%s] saved!", recommendation.id)

    # Return the location of the new Recommendation
    location_url = url_for(
        "get_recommendations", recommendation_id=recommendation.id, _external=True
    )

    return (
        jsonify(recommendation.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


#####################################################################
# UPDATE AN EXISTING RECOMMENDATION
######################################################################
@app.route("/recommendations/<int:recommendation_id>", methods=["PUT"])
def update_recommendation(recommendation_id: int):
    """
    Update an existing recommendation's editable fields.

    Endpoint:
        PUT /recommendations/<recommendation_id>

    Request Body (application/json):
        {
          "recommendation_type": "up-sell" | "cross-sell" | "accessory",   # optional
          "confidence_score": 0.0..1.0,                                   # optional
            "status": "active" | "inactive",                                 # optional
        }
        At least one of the above fields must be provided.
        Values are normalized/validated in the model; confidence_score must be in [0, 1].
    """
    app.logger.info("Request to Update recommendation with id: %s", recommendation_id)
    check_content_type("application/json")
    rec = Recommendation.find(recommendation_id)
    if rec is None:
        return (
            jsonify({"message": "Recommendation not found"}),
            status.HTTP_404_NOT_FOUND,
        )

    data = request.get_json() or {}
    if not data:  # {} or None after get_json
        return (
            jsonify({"message": "At least one field is required"}),
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        rec.update(data)  # model handles normalization + validation
    except DataValidationError as e:
        return jsonify({"message": str(e)}), status.HTTP_400_BAD_REQUEST

    return jsonify(rec.serialize()), status.HTTP_200_OK


#####################################################################
# DELETE A RECOMMENDATION
######################################################################
@app.route("/recommendations/<int:recommendation_id>", methods=["DELETE"])
def delete_recommendations(recommendation_id):
    """
    Delete a Recommendation

    This endpoint will delete a Recommendation based the id specified in the path
    """
    app.logger.info(
        "Request to Delete a recommendation with id [%s]", recommendation_id
    )

    # Delete the Recommendation if it exists
    recommendation = Recommendation.find(recommendation_id)
    if recommendation:
        app.logger.info("Recommendation with ID: %d found.", recommendation.id)
        recommendation.delete()

    app.logger.info("Recommendation with ID: %d delete complete.", recommendation_id)
    return {}, status.HTTP_204_NO_CONTENT


#####################################################################
# READ A Recommendation
######################################################################
@app.route("/recommendations/<int:recommendation_id>", methods=["GET"])
def get_recommendations(recommendation_id):
    """
    Retrieve a single Recommendation

    This endpoint will return a Recommendation based on it's id
    """
    app.logger.info(
        "Request to Retrieve a Recommendation with id [%s]", recommendation_id
    )

    # Attempt to find the Recommendation and abort if not found
    recommendation = Recommendation.find(recommendation_id)
    if not recommendation:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Recommendation with id '{recommendation_id}' was not found.",
        )

    app.logger.info("Returning recommendation: %s", recommendation.id)
    return jsonify(recommendation.serialize()), status.HTTP_200_OK


######################################################################
# LIST RECOMMENDATIONS - Multiple Filters
######################################################################
@app.route("/recommendations", methods=["GET"])
def list_recommendations():
    """Returns recommendations
    Supported query params (all optional, and can be combined):
      - base_product_id: int
      - recommendation_type: "cross-sell", "up-sell", "accessory" (case-insensitive)
      - status: "active", "inactive" (case-insensitive)
      - confidence_score: float in [0, 1]  (minimum threshold, inclusive)
    """
    app.logger.info("Request for recommendation list")

    # Parse args
    base_product_id = request.args.get("base_product_id", type=int)
    recommendation_type = request.args.get("recommendation_type", type=str)
    confidence_score = request.args.get("confidence_score", type=float)
    rec_status = request.args.get("status", type=str)

    # Validate confidence_score range if provided
    if confidence_score is not None:
        if confidence_score < 0 or confidence_score > 1:
            return (
                jsonify({"message": "confidence_score must be in [0, 1]"}),
                status.HTTP_400_BAD_REQUEST,
            )

    # If no filters at all, return all
    if (
        base_product_id is None
        and not recommendation_type
        and not rec_status
        and confidence_score is None
    ):
        app.logger.info("Find all")
        recs = Recommendation.all()
        results = [r.serialize() for r in recs]
        app.logger.info("Returning %d recommendations", len(results))
        return jsonify(results), status.HTTP_200_OK

    # combined filters (AND)
    q = Recommendation.filter_many(
        base_product_id=base_product_id,
        recommendation_type=recommendation_type,
        status=rec_status,
        min_confidence=confidence_score,
    )
    rows = q.all()
    results = [r.serialize() for r in rows]
    app.logger.info("Returning %d recommendations", len(results))
    return jsonify(results), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


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
