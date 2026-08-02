from flask import Blueprint, current_app, g, jsonify, request

from app.dependencies import parse_body, require_admin, require_auth
from app.schemas.user import DriverUserCreate, UserCreate, UserUpdate
from app.services.user_service import (
    create_driver_user_account,
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    update_user,
)

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users_bp.route("/", methods=["GET"])
@require_auth
def get_users():
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 10, type=int)
    role = request.args.get("role")
    db = current_app.mongodb
    return jsonify(list_users(db, page=page, size=size, role=role)), 200


@users_bp.route("/", methods=["POST"])
@require_admin
def create_user_route():
    payload = parse_body(UserCreate)
    db = current_app.mongodb
    return jsonify(create_user(db, payload)), 201


@users_bp.route("/driver-account", methods=["POST"])
@require_admin
def create_driver_user_account_route():
    payload = parse_body(DriverUserCreate)
    db = current_app.mongodb
    return jsonify(create_driver_user_account(db, payload)), 201


@users_bp.route("/<user_id>", methods=["GET"])
@require_auth
def get_user(user_id):
    db = current_app.mongodb
    user = get_user_by_id(db, user_id)
    if not user:
        return jsonify({"detail": "Utilisateur introuvable."}), 404
    return jsonify(user), 200


@users_bp.route("/<user_id>", methods=["PUT"])
@require_admin
def update_user_route(user_id):
    payload = parse_body(UserUpdate)
    db = current_app.mongodb
    return jsonify(update_user(db, user_id, payload)), 200


@users_bp.route("/<user_id>", methods=["DELETE"])
@require_admin
def delete_user_route(user_id):
    db = current_app.mongodb
    delete_user(db, user_id)
    return "", 204

