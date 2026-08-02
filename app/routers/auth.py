from flask import Blueprint, current_app, jsonify, request

from app.services.auth_service import login, refresh_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/login", methods=["POST"])
def login_route():
    # Accept both form-data and JSON
    if request.content_type and "application/json" in request.content_type:
        data = request.get_json(silent=True) or {}
        username = data.get("username") or data.get("email")
        password = data.get("password")
    else:
        username = request.form.get("username") or request.form.get("email")
        password = request.form.get("password")

    db = current_app.mongodb
    result = login(db, username, password)
    return jsonify(result), 200


@auth_bp.route("/refresh", methods=["POST"])
def refresh_route():
    data = request.get_json(silent=True) or {}
    refresh_tok = data.get("refresh_token")
    db = current_app.mongodb
    result = refresh_token(db, refresh_tok)
    return jsonify(result), 200



