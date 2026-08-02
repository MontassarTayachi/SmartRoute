from flask import Blueprint, current_app, jsonify, request

from app.dependencies import parse_body, require_auth
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.services.vehicle_service import (
    create_vehicle,
    delete_vehicle,
    get_vehicle_by_id,
    list_unassigned_vehicles,
    list_vehicles,
    update_vehicle,
)

vehicles_bp = Blueprint("vehicles", __name__, url_prefix="/api/v1/vehicles")


@vehicles_bp.route("/", methods=["GET"])
@require_auth
def get_vehicles():
    status = request.args.get("status")
    vehicle_list_id = request.args.get("vehicle_list_id")
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 10, type=int)
    db = current_app.mongodb
    return jsonify(list_vehicles(db, page=page, size=size, status=status, vehicle_list_id=vehicle_list_id)), 200


@vehicles_bp.route("/", methods=["POST"])
@require_auth
def create_vehicle_route():
    payload = parse_body(VehicleCreate)
    db = current_app.mongodb
    return jsonify(create_vehicle(db, payload)), 201


@vehicles_bp.route("/dispo", methods=["GET"])
def get_available_vehicles():
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 10, type=int)
    db = current_app.mongodb
    return jsonify(list_unassigned_vehicles(db, page=page, size=size)), 200


@vehicles_bp.route("/<vehicle_id>", methods=["GET"])
@require_auth
def get_vehicle_route(vehicle_id):
    db = current_app.mongodb
    vehicle = get_vehicle_by_id(db, vehicle_id)
    if not vehicle:
        return jsonify({"detail": "Véhicule introuvable."}), 404
    return jsonify(vehicle), 200


@vehicles_bp.route("/<vehicle_id>", methods=["PUT"])
@require_auth
def update_vehicle_route(vehicle_id):
    payload = parse_body(VehicleUpdate)
    db = current_app.mongodb
    return jsonify(update_vehicle(db, vehicle_id, payload)), 200


@vehicles_bp.route("/<vehicle_id>", methods=["DELETE"])
@require_auth
def delete_vehicle_route(vehicle_id):
    db = current_app.mongodb
    delete_vehicle(db, vehicle_id)
    return "", 204

