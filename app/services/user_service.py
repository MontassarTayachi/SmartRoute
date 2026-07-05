from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

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


async def create_user(db: AsyncIOMotorDatabase, payload: UserCreate) -> dict:
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
        result = await db["users"].insert_one(document)
        document["_id"] = result.inserted_id
        return _format_user(document)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un utilisateur avec cet email existe déjà.")


async def create_driver_user_account(db: AsyncIOMotorDatabase, payload: DriverUserCreate) -> dict:
    if not ObjectId.is_valid(payload.driver_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conducteur introuvable.")

    driver = await db["drivers"].find_one({"_id": ObjectId(payload.driver_id)})
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conducteur introuvable.")
    if driver.get("login_user_id"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce conducteur a déjà un compte utilisateur associé.",
        )

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
        result = await db["users"].insert_one(document)
        document["_id"] = result.inserted_id
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un utilisateur avec cet email existe déjà.")

    update_result = await db["drivers"].update_one(
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
        await db["users"].delete_one({"_id": document["_id"]})
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Le conducteur est déjà lié à un compte utilisateur.",
        )

    return _format_user(document)


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> dict | None:
    if not ObjectId.is_valid(user_id):
        return None
    document = await db["users"].find_one({"_id": ObjectId(user_id)})
    return _format_user(document) if document else None


async def list_users(db: AsyncIOMotorDatabase, page: int = 1, size: int = 10, role: str | None = None) -> dict:
    skip = max(page - 1, 0) * size
    query = {}
    if role:
        query["role"] = role

    cursor = db["users"].find(query).skip(skip).limit(size)
    items = [
        _format_user(doc)
        for doc in await cursor.to_list(length=size)
    ]
    total = await db["users"].count_documents(query)
    return {"items": items, "total": total, "page": page, "size": size}


async def update_user(db: AsyncIOMotorDatabase, user_id: str, payload: UserUpdate) -> dict:
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items() if k != "password"}
    if payload.password:
        update_data["password_hash"] = hash_password(payload.password)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucune donnée à mettre à jour.")

    update_data["updated_at"] = datetime.utcnow()
    try:
        updated = await db["users"].find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True,
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cet email est déjà utilisé.")

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
    return _format_user(updated)


async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> None:
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    update_driver_result = await db["drivers"].update_one(
        {"login_user_id": ObjectId(user_id)},
        {"$unset": {"login_user_id": ""}},
    )
    result = await db["users"].delete_one({"_id": ObjectId(user_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
