from flask import Blueprint, current_app, jsonify

from app.dependencies import require_auth
from app.services.location_service import list_live_vehicle_locations

vehicles_live_bp = Blueprint("vehicles_live", __name__, url_prefix="/api/v1/vehicles")


@vehicles_live_bp.route("/live", methods=["GET"])
@require_auth
def list_live_vehicles_route():
    db = current_app.mongodb
    return jsonify(list_live_vehicle_locations(db)), 200

