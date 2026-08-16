from flask import Blueprint, current_app, g, jsonify

from app.dependencies import parse_body, require_admin
from app.schemas.optimization import (
    AlgorithmActivationRequest,
    RegionSettingsUpdateRequest,
    RouteStrategyActivationRequest,
)
from app.services.optimization_settings_service import OptimizationSettingsService

admin_optimization_bp = Blueprint("admin_optimization", __name__, url_prefix="/api/admin/optimization")


@admin_optimization_bp.route("/region-settings", methods=["GET"])
@require_admin
def get_region_settings():
    service = OptimizationSettingsService(current_app.mongodb)
    settings = service.get_region_settings()
    if not settings:
        return jsonify({"n_clusters": 5, "mode": "fixe", "updated_by": None, "updated_at": None}), 200
    return jsonify(settings), 200


@admin_optimization_bp.route("/region-settings", methods=["PUT"])
@require_admin
def update_region_settings():
    payload = parse_body(RegionSettingsUpdateRequest)
    service = OptimizationSettingsService(current_app.mongodb)
    updated = service.update_region_settings(
        n_clusters=payload.n_clusters,
        mode=payload.mode,
        updated_by=g.current_user.get("_id"),
    )
    return jsonify(updated), 200


@admin_optimization_bp.route("/algorithms", methods=["GET"])
@require_admin
def list_algorithms():
    service = OptimizationSettingsService(current_app.mongodb)
    return jsonify({"items": service.list_algorithms()}), 200


@admin_optimization_bp.route("/algorithms/activate", methods=["POST"])
@require_admin
def activate_algorithm():
    payload = parse_body(AlgorithmActivationRequest)
    service = OptimizationSettingsService(current_app.mongodb)
    updated = service.activate_algorithm(
        algorithm_name=payload.algorithm_name,
        parameters=payload.parameters,
        updated_by=g.current_user.get("_id"),
    )
    return jsonify(updated), 200


@admin_optimization_bp.route("/route-strategies", methods=["GET"])
@require_admin
def list_route_strategies():
    service = OptimizationSettingsService(current_app.mongodb)
    return jsonify({"items": service.list_route_strategies()}), 200


@admin_optimization_bp.route("/route-strategies/activate", methods=["POST"])
@require_admin
def activate_route_strategy():
    payload = parse_body(RouteStrategyActivationRequest)
    service = OptimizationSettingsService(current_app.mongodb)
    updated = service.activate_route_strategy(
        strategy_name=payload.strategy_name,
        parameters=payload.parameters,
        updated_by=g.current_user.get("_id"),
    )
    return jsonify(updated), 200