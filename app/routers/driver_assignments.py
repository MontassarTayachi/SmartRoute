from flask import Blueprint, current_app, jsonify

from app.dependencies import parse_body, require_auth
from app.schemas.driver import AssignVehicleRequest
from app.services.driver_service import assign_vehicle_to_driver

driver_assignments_bp = Blueprint("driver_assignments", __name__, url_prefix="/api/v1/drivers")


@driver_assignments_bp.route("/<driver_id>/assign_vehicle", methods=["POST"])
@require_auth
def assign_vehicle_to_driver_route(driver_id):
    payload = parse_body(AssignVehicleRequest)
    db = current_app.mongodb
    return jsonify(assign_vehicle_to_driver(db, driver_id, payload)), 200

