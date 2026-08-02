from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from flask_socketio import emit

from app.dependencies import parse_body, require_auth
from app.schemas.tracking import VehicleLocationWrite
from app.services.tracking_service import (
    get_vehicle_latest_location,
    list_latest_vehicle_locations,
    list_vehicle_location_history,
    save_vehicle_location,
)

tracking_bp = Blueprint("tracking", __name__, url_prefix="/api/v1")


@tracking_bp.route("/vehicles/<vehicle_id>/location", methods=["POST"])
@require_auth
def post_vehicle_location_route(vehicle_id):
    payload = parse_body(VehicleLocationWrite)
    db = current_app.mongodb
    location = save_vehicle_location(db, vehicle_id=vehicle_id, payload=payload)
    # Broadcast updated location to all SocketIO tracking clients
    from app.socket_manager import socketio
    socketio.emit("location_update", location, namespace="/tracking")
    return jsonify(location), 200


@tracking_bp.route("/vehicles/<vehicle_id>/location", methods=["GET"])
@require_auth
def get_vehicle_location_route(vehicle_id):
    db = current_app.mongodb
    return jsonify(get_vehicle_latest_location(db, vehicle_id=vehicle_id)), 200


@tracking_bp.route("/vehicles/locations", methods=["GET"])
@require_auth
def get_all_vehicle_locations_route():
    db = current_app.mongodb
    return jsonify(list_latest_vehicle_locations(db)), 200


@tracking_bp.route("/vehicles/<vehicle_id>/locations/history", methods=["GET"])
@require_auth
def get_vehicle_location_history_route(vehicle_id):
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 100, type=int)
    limit = max(1, min(limit, 1000))
    db = current_app.mongodb
    return jsonify(list_vehicle_location_history(db, vehicle_id=vehicle_id, page=page, limit=limit)), 200


# ---------------------------------------------------------------------------
# SocketIO events — registered in main.py via register_tracking_socket(socketio)
# ---------------------------------------------------------------------------

def register_tracking_socket(socketio):
    """Register SocketIO event handlers for the /tracking namespace."""

    @socketio.on("connect", namespace="/tracking")
    def on_tracking_connect():
        db = current_app.mongodb
        locations = list_latest_vehicle_locations(db)
        for location in locations:
            emit("location_update", location)

    @socketio.on("disconnect", namespace="/tracking")
    def on_tracking_disconnect():
        pass



class VehicleTrackingConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

