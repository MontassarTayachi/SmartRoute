from datetime import datetime

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import APIException
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


def create_vehicle(db: Database, payload: VehicleCreate) -> dict:
    if not ObjectId.is_valid(payload.vehicle_list_id):
        raise APIException(400, "ID vehicleListe invalide.")

    vehicle_list = db["vehicleListe"].find_one({"_id": ObjectId(payload.vehicle_list_id)})
    if not vehicle_list:
        raise APIException(404, "vehicleListe introuvable.")

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
        result = db["vehicles"].insert_one(document)
        document["_id"] = result.inserted_id
        return _format_vehicle(document)
    except DuplicateKeyError:
        raise APIException(409, "Un véhicule avec cette immatriculation existe déjà.")


def get_vehicle_by_id(db: Database, vehicle_id: str) -> dict | None:
    if not ObjectId.is_valid(vehicle_id):
        return None
    document = db["vehicles"].find_one({"_id": ObjectId(vehicle_id)})
    return _format_vehicle(document) if document else None


def _format_vehicle_dispo(doc: dict, vehicle_list_doc: dict | None = None) -> dict:
    vehicle_list_id = doc.get("vehicle_list_id")
    return {
        "_id": str(doc["_id"]),
        "registration": doc.get("registration"),
        "vehicle_list_id": str(vehicle_list_id) if vehicle_list_id else None,
        "capacity_kg": doc.get("capacity_kg"),
        "status": doc.get("status"),
        "avg_fuel_consumption": doc.get("avg_fuel_consumption"),
        "created_at": doc.get("created_at"),
        "nom": vehicle_list_doc.get("nom") if vehicle_list_doc else None,
        "image_url": vehicle_list_doc.get("image_url") if vehicle_list_doc else None,
    }


def list_unassigned_vehicles(db: Database, page: int = 1, size: int = 10) -> dict:
    assigned_vehicle_ids = [
        vehicle_id
        for vehicle_id in db["drivers"].distinct("assigned_vehicle_id")
        if vehicle_id is not None
    ]
    query = {"_id": {"$nin": assigned_vehicle_ids}}
    skip = max(page - 1, 0) * size

    vehicles = list(db["vehicles"].find(query).skip(skip).limit(size))

    vehicle_list_ids = list(
        {vehicle["vehicle_list_id"] for vehicle in vehicles if vehicle.get("vehicle_list_id")}
    )
    vehicle_lists: dict = {}
    if vehicle_list_ids:
        for doc in db["vehicleListe"].find({"_id": {"$in": vehicle_list_ids}}):
            vehicle_lists[doc["_id"]] = doc

    items = [
        _format_vehicle_dispo(vehicle, vehicle_lists.get(vehicle.get("vehicle_list_id")))
        for vehicle in vehicles
    ]
    total = db["vehicles"].count_documents(query)
    return {"items": items, "total": total, "page": page, "size": size}


def list_vehicles(
    db: Database,
    page: int = 1,
    size: int = 10,
    status: str | None = None,
    vehicle_list_id: str | None = None,
) -> dict:
    skip = max(page - 1, 0) * size
    query = {}
    if status:
        query["status"] = status
    if vehicle_list_id:
        if ObjectId.is_valid(vehicle_list_id):
            query["vehicle_list_id"] = ObjectId(vehicle_list_id)
        else:
            return {"items": [], "total": 0, "page": page, "size": size}

    items = [_format_vehicle(doc) for doc in db["vehicles"].find(query).skip(skip).limit(size)]
    total = db["vehicles"].count_documents(query)
    return {"items": items, "total": total, "page": page, "size": size}


def update_vehicle(db: Database, vehicle_id: str, payload: VehicleUpdate) -> dict:
    if not ObjectId.is_valid(vehicle_id):
        raise APIException(404, "Véhicule introuvable.")

    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}

    if "vehicle_list_id" in update_data and update_data["vehicle_list_id"]:
        if not ObjectId.is_valid(update_data["vehicle_list_id"]):
            raise APIException(400, "ID vehicleListe invalide.")
        vehicle_list = db["vehicleListe"].find_one({"_id": ObjectId(update_data["vehicle_list_id"])})
        if not vehicle_list:
            raise APIException(404, "vehicleListe introuvable.")
        update_data["vehicle_list_id"] = ObjectId(update_data["vehicle_list_id"])

    if not update_data:
        raise APIException(400, "Aucune donnée à mettre à jour.")
    update_data["updated_at"] = datetime.utcnow()
    try:
        updated = db["vehicles"].find_one_and_update(
            {"_id": ObjectId(vehicle_id)},
            {"$set": update_data},
            return_document=True,
        )
    except DuplicateKeyError:
        raise APIException(409, "Cette immatriculation est déjà utilisée.")

    if not updated:
        raise APIException(404, "Véhicule introuvable.")
    return _format_vehicle(updated)


def delete_vehicle(db: Database, vehicle_id: str) -> None:
    if not ObjectId.is_valid(vehicle_id):
        raise APIException(404, "Véhicule introuvable.")

    result = db["vehicles"].delete_one({"_id": ObjectId(vehicle_id)})
    if result.deleted_count == 0:
        raise APIException(404, "Véhicule introuvable.")


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

