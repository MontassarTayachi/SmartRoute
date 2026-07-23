from __future__ import annotations

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.schemas.location import LocationCreate


def _to_object_id(value: str, *, field_name: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Identifiant {field_name} invalide.",
        )
    return ObjectId(value)


def _format_location(doc: dict) -> dict:
    return {
        "_id": str(doc["_id"]),
        "vehicle_id": str(doc["vehicle_id"]),
        "lat": doc.get("lat"),
        "lng": doc.get("lng"),
        "speed_kmh": doc.get("speed_kmh"),
        "heading": doc.get("heading"),
        "timestamp": doc.get("timestamp"),
    }


async def create_location(db: AsyncIOMotorDatabase, payload: LocationCreate) -> dict:
    vehicle_oid = _to_object_id(payload.vehicle_id, field_name="vehicule")

    try:
        vehicle = await db["vehicles"].find_one({"_id": vehicle_oid}, {"_id": 1})
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicule introuvable.")

        document = {
            "vehicle_id": vehicle_oid,
            "lat": payload.lat,
            "lng": payload.lng,
            "speed_kmh": payload.speed_kmh,
            "heading": payload.heading,
            "timestamp": payload.timestamp,
        }
        result = await db["locations"].insert_one(document)
        document["_id"] = result.inserted_id
        return _format_location(document)
    except HTTPException:
        raise
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflit lors de la creation de la position GPS.",
        )
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur base de donnees lors de la creation de la position GPS.",
        )


async def list_live_vehicle_locations(db: AsyncIOMotorDatabase) -> list[dict]:
    pipeline = [
        {"$sort": {"timestamp": -1}},
        {
            "$group": {
                "_id": "$vehicle_id",
                "lat": {"$first": "$lat"},
                "lng": {"$first": "$lng"},
                "speed_kmh": {"$first": "$speed_kmh"},
                "timestamp": {"$first": "$timestamp"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "vehicle_id": {"$toString": "$_id"},
                "lat": 1,
                "lng": 1,
                "speed_kmh": 1,
                "timestamp": 1,
            }
        },
    ]

    try:
        return await db["locations"].aggregate(pipeline).to_list(length=None)
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur base de donnees lors de la lecture des positions en direct.",
        )
