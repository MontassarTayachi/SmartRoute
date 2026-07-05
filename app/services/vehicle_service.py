from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.schemas.vehicle import VehicleCreate, VehicleUpdate

def _format_vehicle(doc: dict) -> dict:
    vehicle_list_id = doc.get("vehicle_list_id")
    return {
        "_id": str(doc["_id"]),
        "registration": doc.get("registration"),
        "vehicle_list_id": str(vehicle_list_id) if vehicle_list_id else None,
        "capacity_kg": doc.get("capacity_kg"),
        "status": doc.get("status"),
        "avg_fuel_consumption": doc.get("avg_fuel_consumption"),
        "created_at": doc.get("created_at"),
    }

async def create_vehicle(db: AsyncIOMotorDatabase, payload: VehicleCreate) -> dict:
    # Vérifier que le vehicle_list_id existe
    if not ObjectId.is_valid(payload.vehicle_list_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID vehicleListe invalide.")
    
    vehicle_list = await db["vehicleListe"].find_one({"_id": ObjectId(payload.vehicle_list_id)})
    if not vehicle_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="vehicleListe introuvable.")
    
    now = datetime.utcnow()
    document = {
        "registration": payload.registration,
        "vehicle_list_id": ObjectId(payload.vehicle_list_id),
        "capacity_kg": payload.capacity_kg,
        "status": payload.status.value,
        "avg_fuel_consumption": payload.avg_fuel_consumption,
        "created_at": now,
    }
    try:
        result = await db["vehicles"].insert_one(document)
        document["_id"] = result.inserted_id
        return _format_vehicle(document)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un véhicule avec cette immatriculation existe déjà.")


async def get_vehicle_by_id(db: AsyncIOMotorDatabase, vehicle_id: str) -> dict | None:
    if not ObjectId.is_valid(vehicle_id):
        return None
    document = await db["vehicles"].find_one({"_id": ObjectId(vehicle_id)})
    return _format_vehicle(document) if document else None


async def list_vehicles(db: AsyncIOMotorDatabase, page: int = 1, size: int = 10, status: str | None = None, vehicle_list_id: str | None = None) -> dict:
    skip = max(page - 1, 0) * size
    query = {}
    if status:
        query["status"] = status
    if vehicle_list_id:
        if ObjectId.is_valid(vehicle_list_id):
            query["vehicle_list_id"] = ObjectId(vehicle_list_id)
        else:
            return {"items": [], "total": 0, "page": page, "size": size}

    cursor = db["vehicles"].find(query).skip(skip).limit(size)
    items = [
        _format_vehicle(doc)
        for doc in await cursor.to_list(length=size)
    ]
    total = await db["vehicles"].count_documents(query)
    return {"items": items, "total": total, "page": page, "size": size}


async def update_vehicle(db: AsyncIOMotorDatabase, vehicle_id: str, payload: VehicleUpdate) -> dict:
    if not ObjectId.is_valid(vehicle_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Véhicule introuvable.")

    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    
    # Valider vehicle_list_id s'il est fourni
    if "vehicle_list_id" in update_data and update_data["vehicle_list_id"]:
        if not ObjectId.is_valid(update_data["vehicle_list_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID vehicleListe invalide.")
        
        vehicle_list = await db["vehicleListe"].find_one({"_id": ObjectId(update_data["vehicle_list_id"])})
        if not vehicle_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="vehicleListe introuvable.")
        
        update_data["vehicle_list_id"] = ObjectId(update_data["vehicle_list_id"])
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucune donnée à mettre à jour.")
    update_data["updated_at"] = datetime.utcnow()
    try:
        updated = await db["vehicles"].find_one_and_update(
            {"_id": ObjectId(vehicle_id)},
            {"$set": update_data},
            return_document=True,
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cette immatriculation est déjà utilisée.")

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Véhicule introuvable.")
    return _format_vehicle(updated)


async def delete_vehicle(db: AsyncIOMotorDatabase, vehicle_id: str) -> None:
    if not ObjectId.is_valid(vehicle_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Véhicule introuvable.")

    result = await db["vehicles"].delete_one({"_id": ObjectId(vehicle_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Véhicule introuvable.")
