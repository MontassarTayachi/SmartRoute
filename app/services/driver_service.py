from datetime import datetime

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import APIException
from app.schemas.driver import AssignVehicleRequest, DriverCreate, DriverUpdate


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


def _format_vehicle_with_list(doc: dict, vehicle_list_doc: dict | None = None) -> dict:
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


def _collect_vehicle_ids(drivers: list[dict]) -> list[ObjectId]:
    vehicle_ids: set[ObjectId] = set()
    for driver in drivers:
        assigned_vehicle_id = driver.get("assigned_vehicle_id")
        if assigned_vehicle_id:
            vehicle_ids.add(assigned_vehicle_id)
        for entry in driver.get("assignment_history", []):
            vehicle_id = entry.get("vehicle_id")
            if vehicle_id:
                vehicle_ids.add(vehicle_id)
    return list(vehicle_ids)


def _load_vehicles_map(db: Database, vehicle_ids: list[ObjectId]) -> dict[ObjectId, dict]:
    if not vehicle_ids:
        return {}

    vehicles = list(db["vehicles"].find({"_id": {"$in": vehicle_ids}}))
    vehicle_list_ids = list({v["vehicle_list_id"] for v in vehicles if v.get("vehicle_list_id")})
    vehicle_lists: dict[ObjectId, dict] = {}
    if vehicle_list_ids:
        for doc in db["vehicleListe"].find({"_id": {"$in": vehicle_list_ids}}):
            vehicle_lists[doc["_id"]] = doc

    return {
        v["_id"]: _format_vehicle_with_list(v, vehicle_lists.get(v.get("vehicle_list_id")))
        for v in vehicles
    }


def _format_assignment_history(history: list, vehicles_map: dict[ObjectId, dict]) -> list[dict]:
    formatted_history = []
    for entry in history:
        vehicle_id = entry.get("vehicle_id")
        formatted_history.append(
            {
                "vehicle_id": str(vehicle_id) if vehicle_id else None,
                "assigned_at": entry.get("assigned_at"),
                "released_at": entry.get("released_at"),
                "vehicle": vehicles_map.get(vehicle_id) if vehicle_id else None,
            }
        )
    return formatted_history


def _format_driver_with_assignments(doc: dict, vehicles_map: dict[ObjectId, dict]) -> dict:
    assigned_vehicle_id = doc.get("assigned_vehicle_id")
    return {
        **_format_driver(doc),
        "assigned_vehicle": vehicles_map.get(assigned_vehicle_id) if assigned_vehicle_id else None,
        "assignment_history": _format_assignment_history(doc.get("assignment_history", []), vehicles_map),
    }


def _format_drivers_with_assignments(db: Database, drivers: list[dict]) -> list[dict]:
    vehicles_map = _load_vehicles_map(db, _collect_vehicle_ids(drivers))
    return [_format_driver_with_assignments(driver, vehicles_map) for driver in drivers]


def _validate_login_user(
    db: Database,
    login_user_id: str | None,
    *,
    exclude_driver_id: str | None = None,
) -> ObjectId | None:
    if not login_user_id:
        return None
    if not ObjectId.is_valid(login_user_id):
        raise APIException(400, "Identifiant utilisateur invalide.")

    user = db["users"].find_one({"_id": ObjectId(login_user_id)})
    if not user:
        raise APIException(404, "Utilisateur introuvable.")
    if user.get("role") != "driver":
        raise APIException(400, "L'utilisateur associé doit avoir le rôle driver.")
    if not user.get("is_active", True):
        raise APIException(400, "L'utilisateur associé est inactif.")

    query: dict = {"login_user_id": ObjectId(login_user_id)}
    if exclude_driver_id:
        if not ObjectId.is_valid(exclude_driver_id):
            raise APIException(404, "Conducteur introuvable.")
        query["_id"] = {"$ne": ObjectId(exclude_driver_id)}

    existing = db["drivers"].find_one(query)
    if existing:
        raise APIException(409, "Cet utilisateur est déjà associé à un autre conducteur.")

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


def create_driver(db: Database, payload: DriverCreate) -> dict:
    login_user_id = _validate_login_user(db, payload.login_user_id)
    document = {
        "full_name": payload.full_name,
        "phone": payload.phone,
        "license_number": payload.license_number,
        "availability": payload.availability.value,
        "assigned_vehicle_id": ObjectId(payload.assigned_vehicle_id) if payload.assigned_vehicle_id else None,
        "login_user_id": login_user_id,
    }
    try:
        result = db["drivers"].insert_one(document)
        document["_id"] = result.inserted_id
        return _format_driver(document)
    except DuplicateKeyError:
        raise APIException(409, "Un conducteur avec ce numéro de permis existe déjà.")


def list_drivers(db: Database, page: int = 1, size: int = 10, availability: str | None = None, paginate: bool = True) -> dict:
    query = {}
    if availability:
        query["availability"] = availability

    if paginate:
        skip = max(page - 1, 0) * size
        drivers = list(db["drivers"].find(query).skip(skip).limit(size))
        items = _format_drivers_with_assignments(db, drivers)
        total = db["drivers"].count_documents(query)
        return {"items": items, "total": total, "page": page, "size": size}
    else:
        drivers = list(db["drivers"].find(query))
        items = _format_drivers_with_assignments(db, drivers)
        return {"items": items}


def list_drivers_without_user_account(
    db: Database,
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

    items = [_format_driver(doc) for doc in db["drivers"].find(query).skip(skip).limit(size)]
    total = db["drivers"].count_documents(query)
    return {"items": items, "total": total, "page": page, "size": size}


def update_driver(db: Database, driver_id: str, payload: DriverUpdate) -> dict:
    if not ObjectId.is_valid(driver_id):
        raise APIException(404, "Conducteur introuvable.")

    if payload.login_user_id is not None:
        _validate_login_user(db, payload.login_user_id, exclude_driver_id=driver_id)

    update_data = _prepare_update_data(payload)
    if not update_data:
        raise APIException(400, "Aucune donnée à mettre à jour.")

    try:
        updated = db["drivers"].find_one_and_update(
            {"_id": ObjectId(driver_id)},
            {"$set": update_data},
            return_document=True,
        )
    except DuplicateKeyError:
        raise APIException(409, "Ce numéro de permis est déjà utilisé.")

    if not updated:
        raise APIException(404, "Conducteur introuvable.")
    return _format_driver(updated)


def _get_driver_or_404(db: Database, driver_id: str) -> dict:
    if not ObjectId.is_valid(driver_id):
        raise APIException(404, "Conducteur introuvable.")
    driver = db["drivers"].find_one({"_id": ObjectId(driver_id)})
    if not driver:
        raise APIException(404, "Conducteur introuvable.")
    return driver


def assign_vehicle_to_driver(db: Database, driver_id: str, payload: AssignVehicleRequest) -> dict:
    driver = _get_driver_or_404(db, driver_id)

    if driver.get("assigned_vehicle_id"):
        raise APIException(409, "Ce conducteur a déjà un véhicule assigné. Désassignez-le d'abord.")

    vehicle_id = payload.vehicle_id
    if not ObjectId.is_valid(vehicle_id):
        raise APIException(400, "Identifiant véhicule invalide.")

    vehicle = db["vehicles"].find_one({"_id": ObjectId(vehicle_id)})
    if not vehicle:
        raise APIException(404, "Véhicule introuvable.")

    if vehicle.get("status") != "available":
        raise APIException(409, "Le véhicule n'est pas disponible pour l'affectation.")

    existing_driver = db["drivers"].find_one({"assigned_vehicle_id": ObjectId(vehicle_id)})
    if existing_driver:
        raise APIException(409, "Ce véhicule est déjà assigné à un autre conducteur.")

    now = datetime.utcnow()
    vehicle_oid = ObjectId(vehicle_id)
    history_entry = {"vehicle_id": vehicle_oid, "assigned_at": now, "released_at": None}

    updated = db["drivers"].find_one_and_update(
        {"_id": ObjectId(driver_id)},
        {
            "$set": {"assigned_vehicle_id": vehicle_oid},
            "$push": {"assignment_history": history_entry},
        },
        return_document=True,
    )
    db["vehicles"].update_one(
        {"_id": vehicle_oid},
        {"$set": {"status": "in_use", "updated_at": now}},
    )
    return _format_driver(updated)


def unassign_vehicle_from_driver(db: Database, driver_id: str) -> dict:
    driver = _get_driver_or_404(db, driver_id)

    assigned_vehicle_id = driver.get("assigned_vehicle_id")
    if not assigned_vehicle_id:
        raise APIException(409, "Ce conducteur n'a aucun véhicule assigné.")

    now = datetime.utcnow()
    history = driver.get("assignment_history", [])
    for entry in reversed(history):
        if entry.get("released_at") is None and entry.get("vehicle_id") == assigned_vehicle_id:
            entry["released_at"] = now
            break

    updated = db["drivers"].find_one_and_update(
        {"_id": ObjectId(driver_id)},
        {"$set": {"assigned_vehicle_id": None, "assignment_history": history}},
        return_document=True,
    )
    db["vehicles"].update_one(
        {"_id": assigned_vehicle_id},
        {"$set": {"status": "available", "updated_at": now}},
    )
    return _format_driver(updated)


def get_driver_and_vehicle_with_current_user_context(
    db: Database,
    login_user_id: str,
) -> tuple[dict | None, dict | None]:
    driver = db["drivers"].find_one({"login_user_id": ObjectId(login_user_id)})

    if not driver:
        return None, None

    vehicle = None
    assigned_vehicle_id = driver.get("assigned_vehicle_id")

    if assigned_vehicle_id:
        vehicle_doc = db["vehicles"].find_one({"_id": assigned_vehicle_id})

        if vehicle_doc:
            vehicle_list_doc = None
            if vehicle_doc.get("vehicle_list_id"):
                vehicle_list_doc = db["vehicleListe"].find_one({"_id": vehicle_doc["vehicle_list_id"]})
            vehicle = _format_vehicle_with_list(vehicle_doc, vehicle_list_doc)

    return _format_driver(driver), vehicle



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


def _format_vehicle_with_list(doc: dict, vehicle_list_doc: dict | None = None) -> dict:
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


def _collect_vehicle_ids(drivers: list[dict]) -> list[ObjectId]:
    vehicle_ids: set[ObjectId] = set()
    for driver in drivers:
        assigned_vehicle_id = driver.get("assigned_vehicle_id")
        if assigned_vehicle_id:
            vehicle_ids.add(assigned_vehicle_id)
        for entry in driver.get("assignment_history", []):
            vehicle_id = entry.get("vehicle_id")
            if vehicle_id:
                vehicle_ids.add(vehicle_id)
    return list(vehicle_ids)

