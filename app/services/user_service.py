from datetime import datetime

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import APIException
from app.core.security import hash_password
from app.schemas.user import DriverUserCreate, UserCreate, UserUpdate


def _format_user(doc: dict) -> dict:
    return {
        "_id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "role": doc["role"],
        "is_active": doc.get("is_active", True),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


def create_user(db: Database, payload: UserCreate) -> dict:
    now = datetime.utcnow()
    document = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": payload.role.value,
        "is_active": payload.is_active,
        "created_at": now,
        "updated_at": now,
    }
    try:
        result = db["users"].insert_one(document)
        document["_id"] = result.inserted_id
        return _format_user(document)
    except DuplicateKeyError:
        raise APIException(409, "Un utilisateur avec cet email existe déjà.")


def create_driver_user_account(db: Database, payload: DriverUserCreate) -> dict:
    if not ObjectId.is_valid(payload.driver_id):
        raise APIException(404, "Conducteur introuvable.")

    driver = db["drivers"].find_one({"_id": ObjectId(payload.driver_id)})
    if not driver:
        raise APIException(404, "Conducteur introuvable.")
    if driver.get("login_user_id"):
        raise APIException(409, "Ce conducteur a déjà un compte utilisateur associé.")

    now = datetime.utcnow()
    document = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": "driver",
        "is_active": payload.is_active,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = db["users"].insert_one(document)
        document["_id"] = result.inserted_id
    except DuplicateKeyError:
        raise APIException(409, "Un utilisateur avec cet email existe déjà.")

    update_result = db["drivers"].update_one(
        {
            "_id": ObjectId(payload.driver_id),
            "$or": [
                {"login_user_id": None},
                {"login_user_id": {"$exists": False}},
            ],
        },
        {"$set": {"login_user_id": document["_id"]}},
    )

    if update_result.modified_count == 0:
        db["users"].delete_one({"_id": document["_id"]})
        raise APIException(409, "Le conducteur est déjà lié à un compte utilisateur.")

    return _format_user(document)


def get_user_by_id(db: Database, user_id: str) -> dict | None:
    if not ObjectId.is_valid(user_id):
        return None
    document = db["users"].find_one({"_id": ObjectId(user_id)})
    return _format_user(document) if document else None


def list_users(db: Database, page: int = 1, size: int = 10, role: str | None = None) -> dict:
    skip = max(page - 1, 0) * size
    query = {}
    if role:
        query["role"] = role

    cursor = db["users"].find(query).skip(skip).limit(size)
    items = [_format_user(doc) for doc in cursor]
    total = db["users"].count_documents(query)
    return {"items": items, "total": total, "page": page, "size": size}


def update_user(db: Database, user_id: str, payload: UserUpdate) -> dict:
    if not ObjectId.is_valid(user_id):
        raise APIException(404, "Utilisateur introuvable.")

    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items() if k != "password"}
    if payload.password:
        update_data["password_hash"] = hash_password(payload.password)
    if not update_data:
        raise APIException(400, "Aucune donnée à mettre à jour.")

    update_data["updated_at"] = datetime.utcnow()
    try:
        updated = db["users"].find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True,
        )
    except DuplicateKeyError:
        raise APIException(409, "Cet email est déjà utilisé.")

    if not updated:
        raise APIException(404, "Utilisateur introuvable.")
    return _format_user(updated)


def delete_user(db: Database, user_id: str) -> None:
    if not ObjectId.is_valid(user_id):
        raise APIException(404, "Utilisateur introuvable.")

    db["drivers"].update_one(
        {"login_user_id": ObjectId(user_id)},
        {"$unset": {"login_user_id": ""}},
    )
    result = db["users"].delete_one({"_id": ObjectId(user_id)})

    if result.deleted_count == 0:
        raise APIException(404, "Utilisateur introuvable.")



def _format_user(doc: dict) -> dict:
    return {
        "_id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "role": doc["role"],
        "is_active": doc.get("is_active", True),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }

