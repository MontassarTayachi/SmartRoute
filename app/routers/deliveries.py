from flask import Blueprint, current_app, jsonify, request

from app.dependencies import parse_body, require_auth
from app.schemas.delivery import (
    DeliveryAssignRequest,
    DeliveryCreate,
    DeliveryRescheduleRequest,
    DeliveryStatusUpdateRequest,
    DeliveryUpdate,
)
from app.services.delivery_service import (
    assign_delivery,
    create_delivery,
    get_delivery_by_id,
    list_deliveries,
    reschedule_delivery,
    update_delivery,
    update_delivery_status,
)

deliveries_bp = Blueprint("deliveries", __name__, url_prefix="/api/v1/deliveries")


@deliveries_bp.route("/", methods=["GET"])
@require_auth
def list_deliveries_route():
    status_filter = request.args.get("status")
    scheduled_at = request.args.get("scheduled_at")
    date = request.args.get("date")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    paginate = request.args.get("paginate", "true").lower() == "true"
    db = current_app.mongodb
    return jsonify(
        list_deliveries(
            db,
            page=page,
            limit=limit,
            status_filter=status_filter,
            date_filter=scheduled_at or date,
            paginate=paginate,
        )
    ), 200


@deliveries_bp.route("/", methods=["POST"])
@require_auth
def create_delivery_route():
    payload = parse_body(DeliveryCreate)
    db = current_app.mongodb
    return jsonify(create_delivery(db, payload)), 201


@deliveries_bp.route("/<delivery_id>", methods=["GET"])
@require_auth
def get_delivery_route(delivery_id):
    db = current_app.mongodb
    return jsonify(get_delivery_by_id(db, delivery_id)), 200


@deliveries_bp.route("/<delivery_id>", methods=["PUT"])
@require_auth
def update_delivery_route(delivery_id):
    payload = parse_body(DeliveryUpdate)
    db = current_app.mongodb
    return jsonify(update_delivery(db, delivery_id, payload)), 200


@deliveries_bp.route("/<delivery_id>/assign", methods=["POST"])
@require_auth
def assign_delivery_route(delivery_id):
    payload = parse_body(DeliveryAssignRequest)
    db = current_app.mongodb
    return jsonify(assign_delivery(db, delivery_id, vehicle_id=payload.vehicle_id, driver_id=payload.driver_id)), 200


@deliveries_bp.route("/<delivery_id>/status", methods=["POST"])
@require_auth
def update_delivery_status_route(delivery_id):
    payload = parse_body(DeliveryStatusUpdateRequest)
    db = current_app.mongodb
    return jsonify(update_delivery_status(db, delivery_id, payload.status.value)), 200


@deliveries_bp.route("/<delivery_id>/reschedule", methods=["POST"])
@require_auth
def reschedule_delivery_route(delivery_id):
    payload = parse_body(DeliveryRescheduleRequest)
    db = current_app.mongodb
    return jsonify(reschedule_delivery(db, delivery_id, payload.scheduled_at)), 200

