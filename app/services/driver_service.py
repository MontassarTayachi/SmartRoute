from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.schemas.driver import DriverCreate, DriverUpdate


def _format_driver(doc: dict) -> dict:
    return {
        "_id": str(doc["_id"]),
        "full_name": doc["full_name"],
        "phone": doc["phone"],
        "license_number": doc["license_number"],
        "availability": doc["availability"],
        "assigned_vehicle_id": str(doc["assigned_vehicle_id"]) if doc.get("assigned_vehicle_id") else None,
        "login_user_id": str(doc["login_user_id"]) if doc.get("login_user_id") else None,
    }


async def _validate_login_user(
    db: AsyncIOMotorDatabase,
    login_user_id: str | None,
    *,
    exclude_driver_id: str | None = None,
) -> ObjectId | None:
    if not login_user_id:
        return None
    if not ObjectId.is_valid(login_user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identifiant utilisateur invalide.")

    user = await db["users"].find_one({"_id": ObjectId(login_user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
    if user.get("role") != "driver":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'utilisateur associé doit avoir le rôle driver.",
        )
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="L'utilisateur associé est inactif.")

    query: dict = {"login_user_id": ObjectId(login_user_id)}
    if exclude_driver_id:
        if not ObjectId.is_valid(exclude_driver_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conducteur introuvable.")
        query["_id"] = {"$ne": ObjectId(exclude_driver_id)}

    existing = await db["drivers"].find_one(query)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cet utilisateur est déjà associé à un autre conducteur.",
        )

    return ObjectId(login_user_id)


def _prepare_update_data(payload: DriverUpdate) -> dict:
    update_data = {}
    for key, value in payload.model_dump(exclude_none=True).items():
        if key in ("assigned_vehicle_id", "login_user_id"):
            update_data[key] = ObjectId(value) if value else None
        elif key == "availability":
            update_data[key] = value.value if hasattr(value, "value") else value
        else:
            update_data[key] = value
    return update_data


async def create_driver(db: AsyncIOMotorDatabase, payload: DriverCreate) -> dict:
    login_user_id = await _validate_login_user(db, payload.login_user_id)
    document = {
        "full_name": payload.full_name,
        "phone": payload.phone,
        "license_number": payload.license_number,
        "availability": payload.availability.value,
        "assigned_vehicle_id": ObjectId(payload.assigned_vehicle_id) if payload.assigned_vehicle_id else None,
        "login_user_id": login_user_id,
    }
    try:
        result = await db["drivers"].insert_one(document)
        document["_id"] = result.inserted_id
        return _format_driver(document)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un conducteur avec ce numéro de permis existe déjà.")


async def list_drivers(db: AsyncIOMotorDatabase, page: int = 1, size: int = 10, availability: str | None = None) -> dict:
    skip = max(page - 1, 0) * size
    query = {}
    if availability:
        query["availability"] = availability

    cursor = db["drivers"].find(query).skip(skip).limit(size)
    items = [
        _format_driver(doc)
        for doc in await cursor.to_list(length=size)
    ]
    total = await db["drivers"].count_documents(query)
    return {"items": items, "total": total, "page": page, "size": size}


async def list_drivers_without_user_account(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    size: int = 10,
    availability: str | None = None,
) -> dict:
    skip = max(page - 1, 0) * size
    query: dict = {
        "$or": [
            {"login_user_id": None},
            {"login_user_id": {"$exists": False}},
        ]
    }
    if availability:
        query = {"$and": [query, {"availability": availability}]}

    cursor = db["drivers"].find(query).skip(skip).limit(size)
    items = [
        _format_driver(doc)
        for doc in await cursor.to_list(length=size)
    ]
    total = await db["drivers"].count_documents(query)
    return {"items": items, "total": total, "page": page, "size": size}


async def update_driver(db: AsyncIOMotorDatabase, driver_id: str, payload: DriverUpdate) -> dict:
    if not ObjectId.is_valid(driver_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conducteur introuvable.")

    if payload.login_user_id is not None:
        await _validate_login_user(db, payload.login_user_id, exclude_driver_id=driver_id)

    update_data = _prepare_update_data(payload)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucune donnée à mettre à jour.")

    try:
        updated = await db["drivers"].find_one_and_update(
            {"_id": ObjectId(driver_id)},
            {"$set": update_data},
            return_document=True,
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce numéro de permis est déjà utilisé.")

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conducteur introuvable.")
    return _format_driver(updated)
