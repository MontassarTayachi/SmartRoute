from __future__ import annotations

from datetime import datetime

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.exceptions import APIException
from app.schemas.tracking import VehicleLocationWrite


def _to_object_id(value: str, *, field_name: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise APIException(400, f"Identifiant {field_name} invalide.")
    return ObjectId(value)


def _format_location(doc: dict) -> dict:
    return {
        "vehicle_id": str(doc["vehicle_id"]),
        "vehicle_name": doc.get("vehicle_name"),
        "driver_name": doc.get("driver_name"),
        "latitude": doc.get("latitude"),
        "longitude": doc.get("longitude"),
        "timestamp": doc.get("timestamp"),
    }


def _build_vehicle_name(db: Database, *, registration: str | None, vehicle_list_id: ObjectId | None) -> str | None:
    if registration:
        return registration
    if not vehicle_list_id:
        return None
    vehicle_list = db["vehicleListe"].find_one({"_id": vehicle_list_id}, {"nom": 1})
    return vehicle_list.get("nom") if vehicle_list else None


def _get_vehicle_and_driver_context(db: Database, *, vehicle_oid: ObjectId) -> tuple[dict | None, str | None, str | None]:
    vehicle = db["vehicles"].find_one(
        {"_id": vehicle_oid},
        {"_id": 1, "registration": 1, "vehicle_list_id": 1},
    )
    if not vehicle:
        return None, None, None

    vehicle_name = _build_vehicle_name(
        db,
        registration=vehicle.get("registration"),
        vehicle_list_id=vehicle.get("vehicle_list_id"),
    )
    driver = db["drivers"].find_one({"assigned_vehicle_id": vehicle_oid}, {"full_name": 1})
    driver_name = driver.get("full_name") if driver else None
    return vehicle, vehicle_name, driver_name


def save_vehicle_location(db: Database, *, vehicle_id: str, payload: VehicleLocationWrite) -> dict:
    vehicle_oid = _to_object_id(vehicle_id, field_name="vehicule")

    try:
        vehicle, vehicle_name, driver_name = _get_vehicle_and_driver_context(db, vehicle_oid=vehicle_oid)
        if not vehicle:
            raise APIException(404, "Vehicule introuvable.")

        history_document = {
            "vehicle_id": vehicle_oid,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "timestamp": payload.timestamp,
            "created_at": datetime.utcnow(),
        }
        db["vehicle_location_history"].insert_one(history_document)

        latest_document = db["vehicle_latest_locations"].find_one_and_update(
            {"vehicle_id": vehicle_oid},
            {
                "$set": {
                    "vehicle_id": vehicle_oid,
                    "latitude": payload.latitude,
                    "longitude": payload.longitude,
                    "timestamp": payload.timestamp,
                    "updated_at": datetime.utcnow(),
                },
                "$setOnInsert": {"created_at": datetime.utcnow()},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        latest_document["vehicle_name"] = vehicle_name
        latest_document["driver_name"] = driver_name
        return _format_location(latest_document)
    except APIException:
        raise
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de l'enregistrement de la position.")


def get_vehicle_latest_location(db: Database, *, vehicle_id: str) -> dict:
    vehicle_oid = _to_object_id(vehicle_id, field_name="vehicule")

    try:
        latest = db["vehicle_latest_locations"].find_one({"vehicle_id": vehicle_oid})
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de la lecture de la position.")

    if not latest:
        raise APIException(404, "Aucune position connue pour ce vehicule.")

    _, vehicle_name, driver_name = _get_vehicle_and_driver_context(db, vehicle_oid=vehicle_oid)
    latest["vehicle_name"] = vehicle_name
    latest["driver_name"] = driver_name

    return _format_location(latest)


def list_latest_vehicle_locations(db: Database) -> list[dict]:
    try:
        latest_docs = list(db["vehicle_latest_locations"].find().sort("timestamp", -1))
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de la lecture des positions des vehicules.")

    if not latest_docs:
        return []

    vehicle_ids = [doc["vehicle_id"] for doc in latest_docs if doc.get("vehicle_id")]
    vehicle_map: dict[ObjectId, dict] = {}
    vehicle_list_map: dict[ObjectId, str] = {}
    driver_map: dict[ObjectId, str] = {}

    try:
        vehicles = list(db["vehicles"].find(
            {"_id": {"$in": vehicle_ids}},
            {"_id": 1, "registration": 1, "vehicle_list_id": 1},
        ))

        for vehicle in vehicles:
            vehicle_map[vehicle["_id"]] = vehicle

        vehicle_list_ids = list(
            {v["vehicle_list_id"] for v in vehicles if v.get("vehicle_list_id")}
        )
        if vehicle_list_ids:
            for vl in db["vehicleListe"].find({"_id": {"$in": vehicle_list_ids}}, {"nom": 1}):
                vehicle_list_map[vl["_id"]] = vl.get("nom")

        for driver in db["drivers"].find(
            {"assigned_vehicle_id": {"$in": vehicle_ids}},
            {"assigned_vehicle_id": 1, "full_name": 1},
        ):
            assigned_vehicle_id = driver.get("assigned_vehicle_id")
            if assigned_vehicle_id:
                driver_map[assigned_vehicle_id] = driver.get("full_name")
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de la lecture des metadonnees vehicules.")

    items: list[dict] = []
    for doc in latest_docs:
        vid = doc.get("vehicle_id")
        vehicle = vehicle_map.get(vid)
        vehicle_name = None
        if vehicle:
            vehicle_name = vehicle.get("registration")
            if not vehicle_name:
                vehicle_name = vehicle_list_map.get(vehicle.get("vehicle_list_id"))

        doc["vehicle_name"] = vehicle_name
        doc["driver_name"] = driver_map.get(vid)
        items.append(_format_location(doc))

    return items


def list_vehicle_location_history(db: Database, *, vehicle_id: str, page: int = 1, limit: int = 100) -> dict:
    vehicle_oid = _to_object_id(vehicle_id, field_name="vehicule")
    page = max(page, 1)
    limit = max(limit, 1)
    skip = (page - 1) * limit

    query = {"vehicle_id": vehicle_oid}

    try:
        docs = list(db["vehicle_location_history"].find(query).sort("timestamp", -1).skip(skip).limit(limit))
        total = db["vehicle_location_history"].count_documents(query)
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de la lecture de l'historique GPS.")

    return {
        "items": [_format_location(doc) for doc in docs],
        "total": total,
        "page": page,
        "limit": limit,
    }



def _to_object_id(value: str, *, field_name: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Identifiant {field_name} invalide.",
        )
    return ObjectId(value)


def _format_location(doc: dict) -> dict:
    return {
        "vehicle_id": str(doc["vehicle_id"]),
        "vehicle_name": doc.get("vehicle_name"),
        "driver_name": doc.get("driver_name"),
        "latitude": doc.get("latitude"),
        "longitude": doc.get("longitude"),
        "timestamp": doc.get("timestamp"),
    }
