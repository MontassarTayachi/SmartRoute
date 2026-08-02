from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from app.dependencies import parse_body, require_auth
from app.schemas.route import RouteOptimizeRequest
from app.services.route_service import get_route_history, optimize_route

routes_bp = Blueprint("routes", __name__, url_prefix="/api/v1/routes")


@routes_bp.route("/history", methods=["GET"])
@require_auth
def get_routes_history_route():
    vehicle_id = request.args.get("vehicle_id")
    from_str = request.args.get("from")
    to_str = request.args.get("to")

    from_dt = datetime.fromisoformat(from_str) if from_str else None
    to_dt = datetime.fromisoformat(to_str) if to_str else None

    db = current_app.mongodb
    return jsonify(get_route_history(db, vehicle_id=vehicle_id, from_dt=from_dt, to_dt=to_dt)), 200


@routes_bp.route("/optimiz", methods=["POST"])
@require_auth
def optimize_route_route():
    payload = parse_body(RouteOptimizeRequest)
    db = current_app.mongodb
    return jsonify(optimize_route(db, delivery_ids=payload.delivery_ids, constraints=payload.constraints)), 200

