from datetime import timedelta
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.schemas.user import UserCreate, UserResponse


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


async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> dict | None:
    user = await db["users"].find_one({"email": email})
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    if not user.get("is_active", True):
        return None
    return _format_user(user)


async def login(db: AsyncIOMotorDatabase, email: str, password: str) -> dict:
    user = await authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe invalide.")

    return {
        "access_token": create_access_token(subject=user["_id"]),
        "refresh_token": create_refresh_token(subject=user["_id"]),
        "token_type": "bearer",
        "user": user,
    }


async def refresh_token(db: AsyncIOMotorDatabase, refresh_token: str) -> dict:
    from app.core.security import decode_token

    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalide.")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide pour le rafraîchissement.")

    user_id = payload.get("sub")
    user = await db["users"].find_one({"_id": user_id})
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Compte introuvable ou inactif.")

    return {
        "access_token": create_access_token(subject=user_id),
        "refresh_token": create_refresh_token(subject=user_id),
        "token_type": "bearer",
    }
