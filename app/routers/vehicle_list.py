from flask import Blueprint, current_app, jsonify, request

from app.dependencies import require_auth
from app.schemas.vehicle_list import VehicleListCreate, VehicleListUpdate
from app.services.vehicle_list_service import (
    create_vehicle_list,
    delete_vehicle_list,
    get_vehicle_list_by_id,
    list_vehicle_list,
    update_vehicle_list,
)

vehicle_list_bp = Blueprint("vehicle_list", __name__, url_prefix="/api/v1/vehicle-list")


@vehicle_list_bp.route("/", methods=["GET"])
@require_auth
def get_vehicle_list():
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 10, type=int)
    db = current_app.mongodb
    return jsonify(list_vehicle_list(db, page=page, size=size)), 200


@vehicle_list_bp.route("/", methods=["POST"])
@require_auth
def create_vehicle_list_route():
    nom = request.form.get("nom")
    if not nom:
        return jsonify({"detail": "Le champ 'nom' est requis."}), 422
    image = request.files.get("image")
    payload = VehicleListCreate(nom=nom)
    db = current_app.mongodb
    return jsonify(create_vehicle_list(db, payload, image_file=image)), 201


@vehicle_list_bp.route("/<item_id>", methods=["GET"])
@require_auth
def get_vehicle_list_item(item_id):
    db = current_app.mongodb
    item = get_vehicle_list_by_id(db, item_id)
    if not item:
        return jsonify({"detail": "Élément introuvable."}), 404
    return jsonify(item), 200


@vehicle_list_bp.route("/<item_id>", methods=["PUT"])
@require_auth
def update_vehicle_list_route(item_id):
    nom = request.form.get("nom")
    image = request.files.get("image")
    payload = VehicleListUpdate(nom=nom)
    db = current_app.mongodb
    return jsonify(update_vehicle_list(db, item_id, payload, image_file=image)), 200


@vehicle_list_bp.route("/<item_id>", methods=["DELETE"])
@require_auth
def delete_vehicle_list_route(item_id):
    db = current_app.mongodb
    delete_vehicle_list(db, item_id)
    return "", 204

