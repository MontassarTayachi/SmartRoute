from __future__ import annotations

from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from typing import Any

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.exceptions import APIException


def _to_object_id(value: str, *, field_name: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise APIException(400, f"Identifiant {field_name} invalide.")
    return ObjectId(value)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return earth_radius_km * c


def get_route_history(
    db: Database,
    *,
    vehicle_id: str | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> list[dict]:
    query: dict[str, Any] = {}

    if vehicle_id:
        query["vehicle_id"] = _to_object_id(vehicle_id, field_name="vehicule")

    if from_dt or to_dt:
        query["timestamp"] = {}
        if from_dt:
            query["timestamp"]["$gte"] = from_dt
        if to_dt:
            query["timestamp"]["$lte"] = to_dt

    try:
        docs = list(db["locations"].find(query).sort("timestamp", 1))
        return [
            {
                "vehicle_id": str(doc["vehicle_id"]),
                "lat": doc.get("lat"),
                "lng": doc.get("lng"),
                "speed_kmh": doc.get("speed_kmh"),
                "heading": doc.get("heading"),
                "timestamp": doc.get("timestamp"),
            }
            for doc in docs
        ]
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de la lecture de l'historique des trajets.")


def optimize_route(db: Database, *, delivery_ids: list[str], constraints: dict[str, Any] | None = None) -> dict:
    if not delivery_ids:
        return {"route": [], "distance_km": 0, "estimated_time": 0}

    constraints = constraints or {}

    object_ids = [_to_object_id(did, field_name="livraison") for did in delivery_ids]

    try:
        deliveries = list(db["deliveries"].find({"_id": {"$in": object_ids}}))
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees pendant l'optimisation d'itineraire.")

    if len(deliveries) != len(object_ids):
        raise APIException(404, "Une ou plusieurs livraisons sont introuvables.")

    deliveries.sort(key=lambda d: (str(d.get("priority", "")), d.get("scheduled_at") or datetime.max))

    route: list[dict[str, Any]] = []
    total_distance = 0.0
    prev_lat = None
    prev_lng = None

    for delivery in deliveries:
        pickup_lat = float(delivery.get("pickup_address_lat"))
        pickup_lng = float(delivery.get("pickup_address_lng"))
        dropoff_lat = float(delivery.get("dropoff_address_lat"))
        dropoff_lng = float(delivery.get("dropoff_address_lng"))

        if prev_lat is not None and prev_lng is not None:
            total_distance += _haversine_km(prev_lat, prev_lng, pickup_lat, pickup_lng)
        total_distance += _haversine_km(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)

        route.append(
            {
                "delivery_id": str(delivery["_id"]),
                "reference": delivery.get("reference"),
                "pickup": {"lat": pickup_lat, "lng": pickup_lng},
                "dropoff": {"lat": dropoff_lat, "lng": dropoff_lng},
                "priority": delivery.get("priority"),
                "scheduled_at": delivery.get("scheduled_at"),
            }
        )
        prev_lat = dropoff_lat
        prev_lng = dropoff_lng

    avg_speed_kmh = float(constraints.get("avg_speed_kmh", 40))
    estimated_time_minutes = int((total_distance / avg_speed_kmh) * 60) if avg_speed_kmh > 0 else 0

    return {
        "route": route,
        "distance_km": round(total_distance, 2),
        "estimated_time": estimated_time_minutes,
    }



def _to_object_id(value: str, *, field_name: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Identifiant {field_name} invalide.",
        )
    return ObjectId(value)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return earth_radius_km * c
