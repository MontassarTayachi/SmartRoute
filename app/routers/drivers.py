from flask import Blueprint, current_app, jsonify, request

from app.core.exceptions import APIException
from app.dependencies import parse_body, require_auth
from app.schemas.driver import AssignVehicleRequest, DriverCreate, DriverUpdate
from app.services.driver_service import (
    assign_vehicle_to_driver,
    create_driver,
    get_driver_and_vehicle_with_current_user_context,
    list_drivers,
    list_drivers_without_user_account,
    unassign_vehicle_from_driver,
    update_driver,
)

drivers_bp = Blueprint("drivers", __name__, url_prefix="/api/v1/drivers")


@drivers_bp.route("/", methods=["GET"])
@require_auth
def get_drivers():
    availability = request.args.get("availability")
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 10, type=int)
    db = current_app.mongodb
    return jsonify(list_drivers(db, page=page, size=size, availability=availability)), 200


@drivers_bp.route("/without-user-account", methods=["GET"])
@require_auth
def get_drivers_without_user_account():
    availability = request.args.get("availability")
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 10, type=int)
    db = current_app.mongodb
    return jsonify(list_drivers_without_user_account(db, page=page, size=size, availability=availability)), 200


# /current must come before /<driver_id> to avoid route capture
@drivers_bp.route("/current", methods=["GET"])
@require_auth
def get_current_driver_route():
    from flask import g
    db = current_app.mongodb
    current_user = g.current_user
    driver, vehicle = get_driver_and_vehicle_with_current_user_context(db, current_user["_id"])
    if driver is None:
        return jsonify({"detail": "Driver not found"}), 404
    return jsonify({"driver": driver, "vehicle": vehicle}), 200


@drivers_bp.route("/", methods=["POST"])
@require_auth
def create_driver_route():
    payload = parse_body(DriverCreate)
    db = current_app.mongodb
    return jsonify(create_driver(db, payload)), 201


@drivers_bp.route("/<driver_id>", methods=["PUT"])
@require_auth
def update_driver_route(driver_id):
    payload = parse_body(DriverUpdate)
    db = current_app.mongodb
    return jsonify(update_driver(db, driver_id, payload)), 200


@drivers_bp.route("/<driver_id>/assign-vehicle", methods=["POST"])
@require_auth
def assign_vehicle_route(driver_id):
    payload = parse_body(AssignVehicleRequest)
    db = current_app.mongodb
    return jsonify(assign_vehicle_to_driver(db, driver_id, payload)), 200


@drivers_bp.route("/<driver_id>/unassign-vehicle", methods=["POST"])
@require_auth
def unassign_vehicle_route(driver_id):
    db = current_app.mongodb
    return jsonify(unassign_vehicle_from_driver(db, driver_id)), 200

