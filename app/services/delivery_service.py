from __future__ import annotations

from datetime import date, datetime, time, timedelta
from uuid import uuid4

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.core.exceptions import APIException
from app.schemas.delivery import DeliveryCreate, DeliveryStatus, DeliveryUpdate


ALLOWED_DELIVERY_STATUSES = {
    DeliveryStatus.pending.value,
    DeliveryStatus.assigned.value,
    DeliveryStatus.in_progress.value,
    DeliveryStatus.delivered.value,
    DeliveryStatus.cancelled.value,
}


def _to_object_id(value: str, *, field_name: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise APIException(400, f"Identifiant {field_name} invalide.")
    return ObjectId(value)


def _normalize_related_document(doc: dict | None) -> dict | None:
    if not doc:
        return None
    normalized = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            normalized[key] = str(value)
        else:
            normalized[key] = value
    if "_id" in normalized:
        normalized["_id"] = str(doc["_id"])
    return normalized


def _format_delivery(doc: dict, *, vehicle: dict | None = None, driver: dict | None = None) -> dict:
    return {
        "_id": str(doc["_id"]),
        "reference": doc.get("reference"),
        "customer": doc.get("customer"),
        "pickup_address": doc.get("pickup_address"),
        "pickup_address_lat": doc.get("pickup_address_lat"),
        "pickup_address_lng": doc.get("pickup_address_lng"),
        "dropoff_address": doc.get("dropoff_address"),
        "dropoff_address_lat": doc.get("dropoff_address_lat"),
        "dropoff_address_lng": doc.get("dropoff_address_lng"),
        "status": doc.get("status"),
        "priority": doc.get("priority"),
        "weight_kg": doc.get("weight_kg"),
        "vehicle_id": str(doc["vehicle_id"]) if doc.get("vehicle_id") else None,
        "driver_id": str(doc["driver_id"]) if doc.get("driver_id") else None,
        "scheduled_at": doc.get("scheduled_at"),
        "delivered_at": doc.get("delivered_at"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "vehicle": _normalize_related_document(vehicle),
        "driver": _normalize_related_document(driver),
    }


def _generate_delivery_reference(db: Database) -> str:
    for _ in range(10):
        reference = f"DLV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        exists = db["deliveries"].find_one({"reference": reference}, {"_id": 1})
        if not exists:
            return reference
    raise APIException(500, "Impossible de générer une référence de livraison unique.")


def _parse_date_filter(date_value: str) -> tuple[datetime, datetime]:
    try:
        parsed_date = date.fromisoformat(date_value)
    except ValueError:
        raise APIException(400, "Le paramètre date doit être au format YYYY-MM-DD.")
    start_of_day = datetime.combine(parsed_date, time.min)
    end_of_day = start_of_day + timedelta(days=1)
    return start_of_day, end_of_day


def list_deliveries(
    db: Database,
    *,
    page: int = 1,
    limit: int = 20,
    status_filter: str | None = None,
    date_filter: str | None = None,
) -> dict:
    page = max(page, 1)
    limit = max(limit, 1)
    skip = (page - 1) * limit

    query: dict = {}
    if status_filter:
        if status_filter not in ALLOWED_DELIVERY_STATUSES:
            raise APIException(400, "Statut de livraison invalide.")
        query["status"] = status_filter

    if date_filter:
        start_of_day, end_of_day = _parse_date_filter(date_filter)
        query["scheduled_at"] = {"$gte": start_of_day, "$lt": end_of_day}

    try:
        docs = list(db["deliveries"].find(query).sort("created_at", -1).skip(skip).limit(limit))
        items = [_format_delivery(doc) for doc in docs]
        total = db["deliveries"].count_documents(query)
        return {"items": items, "total": total, "page": page, "limit": limit}
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de la lecture des livraisons.")


def create_delivery(db: Database, payload: DeliveryCreate) -> dict:
    now = datetime.utcnow()
    reference = _generate_delivery_reference(db)

    document = {
        "reference": reference,
        "customer": payload.customer,
        "pickup_address": payload.pickup_address,
        "pickup_address_lat": payload.pickup_address_lat,
        "pickup_address_lng": payload.pickup_address_lng,
        "dropoff_address": payload.dropoff_address,
        "dropoff_address_lat": payload.dropoff_address_lat,
        "dropoff_address_lng": payload.dropoff_address_lng,
        "status": DeliveryStatus.pending.value,
        "priority": payload.priority,
        "weight_kg": payload.weight_kg,
        "vehicle_id": None,
        "driver_id": None,
        "scheduled_at": payload.scheduled_at,
        "delivered_at": None,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = db["deliveries"].insert_one(document)
        document["_id"] = result.inserted_id
        return _format_delivery(document)
    except DuplicateKeyError:
        raise APIException(409, "Une livraison avec cette reference existe deja.")
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de la creation de la livraison.")


def get_delivery_by_id(db: Database, delivery_id: str) -> dict:
    delivery_oid = _to_object_id(delivery_id, field_name="livraison")

    try:
        delivery = db["deliveries"].find_one({"_id": delivery_oid})
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de la lecture de la livraison.")

    if not delivery:
        raise APIException(404, "Livraison introuvable.")

    vehicle = None
    driver = None
    try:
        if delivery.get("vehicle_id"):
            vehicle = db["vehicles"].find_one({"_id": delivery["vehicle_id"]})
        if delivery.get("driver_id"):
            driver = db["drivers"].find_one({"_id": delivery["driver_id"]})
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors du chargement des relations.")

    return _format_delivery(delivery, vehicle=vehicle, driver=driver)


def update_delivery(db: Database, delivery_id: str, payload: DeliveryUpdate) -> dict:
    delivery_oid = _to_object_id(delivery_id, field_name="livraison")

    update_data = payload.model_dump(exclude_none=True)
    if "vehicle_id" in update_data:
        update_data["vehicle_id"] = _to_object_id(update_data["vehicle_id"], field_name="vehicule")
    if "driver_id" in update_data:
        update_data["driver_id"] = _to_object_id(update_data["driver_id"], field_name="conducteur")

    if not update_data:
        raise APIException(400, "Aucune donnee a mettre a jour.")

    update_data["updated_at"] = datetime.utcnow()

    try:
        updated = db["deliveries"].find_one_and_update(
            {"_id": delivery_oid},
            {"$set": update_data},
            return_document=True,
        )
    except DuplicateKeyError:
        raise APIException(409, "Conflit de donnees sur la livraison.")
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de la mise a jour de la livraison.")

    if not updated:
        raise APIException(404, "Livraison introuvable.")
    return _format_delivery(updated)


def assign_delivery(db: Database, delivery_id: str, *, vehicle_id: str, driver_id: str) -> dict:
    delivery_oid = _to_object_id(delivery_id, field_name="livraison")
    vehicle_oid = _to_object_id(vehicle_id, field_name="vehicule")
    driver_oid = _to_object_id(driver_id, field_name="conducteur")

    try:
        delivery = db["deliveries"].find_one({"_id": delivery_oid})
        if not delivery:
            raise APIException(404, "Livraison introuvable.")

        vehicle = db["vehicles"].find_one({"_id": vehicle_oid})
        if not vehicle:
            raise APIException(404, "Vehicule introuvable.")

        driver = db["drivers"].find_one({"_id": driver_oid})
        if not driver:
            raise APIException(404, "Conducteur introuvable.")

        updated = db["deliveries"].find_one_and_update(
            {"_id": delivery_oid},
            {
                "$set": {
                    "vehicle_id": vehicle_oid,
                    "driver_id": driver_oid,
                    "status": DeliveryStatus.assigned.value,
                    "updated_at": datetime.utcnow(),
                }
            },
            return_document=True,
        )
    except APIException:
        raise
    except DuplicateKeyError:
        raise APIException(409, "Conflit lors de l'affectation de la livraison.")
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors de l'affectation.")

    return _format_delivery(updated, vehicle=vehicle, driver=driver)


def update_delivery_status(db: Database, delivery_id: str, status_value: str) -> dict:
    delivery_oid = _to_object_id(delivery_id, field_name="livraison")
    if status_value not in ALLOWED_DELIVERY_STATUSES:
        raise APIException(400, "Statut de livraison invalide.")

    update_data: dict = {"status": status_value, "updated_at": datetime.utcnow()}
    if status_value == DeliveryStatus.delivered.value:
        update_data["delivered_at"] = datetime.utcnow()

    try:
        updated = db["deliveries"].find_one_and_update(
            {"_id": delivery_oid},
            {"$set": update_data},
            return_document=True,
        )
    except PyMongoError:
        raise APIException(500, "Erreur base de donnees lors du changement de statut.")

    if not updated:
        raise APIException(404, "Livraison introuvable.")
    return _format_delivery(updated)



ALLOWED_DELIVERY_STATUSES = {
    DeliveryStatus.pending.value,
    DeliveryStatus.assigned.value,
    DeliveryStatus.in_progress.value,
    DeliveryStatus.delivered.value,
    DeliveryStatus.cancelled.value,
}


def _to_object_id(value: str, *, field_name: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Identifiant {field_name} invalide.",
        )
    return ObjectId(value)


def _normalize_related_document(doc: dict | None) -> dict | None:
    if not doc:
        return None

    normalized = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            normalized[key] = str(value)
        else:
            normalized[key] = value

    if "_id" in normalized:
        normalized["_id"] = str(doc["_id"])
    return normalized


def _format_delivery(
    doc: dict,
    *,
    vehicle: dict | None = None,
    driver: dict | None = None,
) -> dict:
    return {
        "_id": str(doc["_id"]),
        "reference": doc.get("reference"),
        "customer": doc.get("customer"),
        "pickup_address": doc.get("pickup_address"),
        "pickup_address_lat": doc.get("pickup_address_lat"),
        "pickup_address_lng": doc.get("pickup_address_lng"),
        "dropoff_address": doc.get("dropoff_address"),
        "dropoff_address_lat": doc.get("dropoff_address_lat"),
        "dropoff_address_lng": doc.get("dropoff_address_lng"),
        "status": doc.get("status"),
        "priority": doc.get("priority"),
        "weight_kg": doc.get("weight_kg"),
        "vehicle_id": str(doc["vehicle_id"]) if doc.get("vehicle_id") else None,
        "driver_id": str(doc["driver_id"]) if doc.get("driver_id") else None,
        "scheduled_at": doc.get("scheduled_at"),
        "delivered_at": doc.get("delivered_at"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "vehicle": _normalize_related_document(vehicle),
        "driver": _normalize_related_document(driver),
    }

