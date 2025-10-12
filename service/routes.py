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

from flask import jsonify, request
from flask import current_app as app  # Import Flask application
from service.models import Recommendation
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


@app.route("/recommendations", methods=["GET"])
def list_recommendations():
    """Return recommendation list with optional filters."""
    app.logger.info("Request for recommendation list")

    # ---- Query params ----
    base_product_id = request.args.get("base_product_id", type=int)
    recommendation_type = request.args.get("recommendation_type", type=str)
    confidence_score = request.args.get("confidence_score", type=float)
    rec_status = request.args.get("status", type=str)
    limit = request.args.get("quantity", default=10, type=int)  # default = 10

    # Normalize simple enums (case-insensitive; keep hyphens)
    if recommendation_type:
        recommendation_type = recommendation_type.strip().lower()
    if rec_status:
        rec_status = rec_status.strip().lower()

    # ---- Build query (AND all provided filters) ----
    query = Recommendation.query
    if base_product_id is not None:
        app.logger.info("Filter base_product_id=%s", base_product_id)
        query = query.filter(Recommendation.base_product_id == base_product_id)
    if recommendation_type:
        app.logger.info("Filter recommendation_type=%s", recommendation_type)
        query = query.filter(
            Recommendation.recommendation_type.ilike(recommendation_type)
        )
    if confidence_score is not None:
        app.logger.info("Filter confidence_score>=%s", confidence_score)
        query = query.filter(Recommendation.confidence_score >= confidence_score)
    if rec_status:
        app.logger.info("Filter status=%s", rec_status)
        query = query.filter(Recommendation.status.ilike(rec_status))

    # ---- Execute ----
    recs = query.limit(max(1, limit)).all()

    if not recs:
        app.logger.info("No recommendations found")
        return (
            jsonify({"message": "Recommendation not found"}),
            status.HTTP_404_NOT_FOUND,
        )

    results = [r.serialize() for r in recs]
    app.logger.info("Returning %d recommendations", len(results))
    return jsonify(results), status.HTTP_200_OK
