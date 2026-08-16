from functools import wraps

from bson import ObjectId
from flask import current_app, g, jsonify, request

from app.core.security import decode_token
from app.services.user_service import get_user_by_id


def _extract_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def get_current_user():
    """Validate JWT and return (user, None) or (None, error_response)."""
    token = _extract_token()
    if not token:
        return None, (jsonify({"detail": "Token manquant."}), 401)

    try:
        payload = decode_token(token)
    except ValueError as exc:
        return None, (jsonify({"detail": str(exc)}), 401)

    if payload.get("type") != "access":
        return None, (jsonify({"detail": "Token invalide pour l'accès."}), 401)

    user_id = payload.get("sub")
    if not user_id or not ObjectId.is_valid(user_id):
        return None, (jsonify({"detail": "Utilisateur introuvable."}), 401)

    db = current_app.mongodb
    user = get_user_by_id(db, user_id)
    if not user or not user.get("is_active"):
        return None, (jsonify({"detail": "Compte inactif ou introuvable."}), 401)

    return user, None


def require_auth(f):
    """Decorator: validates JWT and stores user in g.current_user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user, error = get_current_user()
        if error:
            return error
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator: validates JWT and enforces admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user, error = get_current_user()
        if error:
            return error
        if user.get("role") != "admin":
            return jsonify({"detail": "Accès réservé aux administrateurs."}), 403
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def parse_body(ModelClass):
    """Parse and validate JSON body against a Pydantic model. Raises APIException on failure."""
    from pydantic import ValidationError
    from app.core.exceptions import APIException
    data = request.get_json(silent=True) or {}
    try:
        return ModelClass(**data)
    except ValidationError as exc:
        # Keep `detail` a JSON array of {loc, msg, type} instead of str(exc.errors())
        # (a Python repr string). The frontend's getApiErrorMessage()
        # (src/utils/apiError.js) explicitly branches on Array.isArray(detail) to
        # render a friendly message per field; a stringified repr defeats that
        # branch and leaks raw Python syntax to the user.
        errors = [
            {
                "loc": list(error.get("loc", ())),
                "msg": error.get("msg", ""),
                "type": error.get("type", ""),
            }
            for error in exc.errors()
        ]
        raise APIException(422, errors)

