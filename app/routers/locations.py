from flask import Blueprint, current_app, jsonify

from app.dependencies import parse_body, require_auth
from app.schemas.location import LocationCreate
from app.services.location_service import create_location

locations_bp = Blueprint("locations", __name__, url_prefix="/api/v1/locations")


@locations_bp.route("/", methods=["POST"])
@require_auth
def create_location_route():
    payload = parse_body(LocationCreate)
    db = current_app.mongodb
    return jsonify(create_location(db, payload)), 201

