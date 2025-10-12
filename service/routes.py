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

from flask import jsonify, request, abort
from flask import current_app as app  # Import Flask application
from service.models import DataValidationError, Recommendation
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
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
    # Todo: uncomment this code when get_recommendations is implemented
    # location_url = url_for(
    #     "get_recommendations", recommendation_id=recommendation.id, _external=True
    # )
    location_url = "unknown"

    return (
        jsonify(recommendation.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


######################################################################
# UPDATE AN EXISTING PET
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
    try:
        rec.update(data)  # model handles normalization + validation
    except DataValidationError as e:
        return jsonify({"message": str(e)}), status.HTTP_400_BAD_REQUEST

    return jsonify(rec.serialize()), status.HTTP_200_OK


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
