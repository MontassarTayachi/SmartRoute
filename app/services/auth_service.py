from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import APIException
from app.core.security import create_access_token, create_refresh_token, verify_password


def _format_user(doc: dict) -> dict:
    return {
        "_id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "role": doc["role"],
        "is_active": doc["is_active"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


def authenticate_user(db: Database, email: str, password: str) -> dict | None:
    user = db["users"].find_one({"email": email})
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    if not user.get("is_active", True):
        return None
    return _format_user(user)


def login(db: Database, email: str, password: str) -> dict:
    user = authenticate_user(db, email, password)
    if not user:
        raise APIException(401, "Email ou mot de passe invalide.")

    return {
        "access_token": create_access_token(subject=user["_id"]),
        "refresh_token": create_refresh_token(subject=user["_id"]),
        "token_type": "bearer",
        "user": user,
    }


def refresh_token(db: Database, refresh_tok: str) -> dict:
    from app.core.security import decode_token

    if not refresh_tok:
        raise APIException(401, "Refresh token manquant.")

    try:
        payload = decode_token(refresh_tok)
    except ValueError:
        raise APIException(401, "Refresh token invalide.")

    if payload.get("type") != "refresh":
        raise APIException(401, "Token invalide pour le rafraîchissement.")

    user_id = payload.get("sub")
    user = db["users"].find_one({"_id": user_id})
    if not user or not user.get("is_active", True):
        raise APIException(401, "Compte introuvable ou inactif.")

    return {
        "access_token": create_access_token(subject=user_id),
        "refresh_token": create_refresh_token(subject=user_id),
        "token_type": "bearer",
    }

