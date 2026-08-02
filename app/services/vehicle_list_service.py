import os
from datetime import datetime
from pathlib import Path

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import APIException
from app.schemas.vehicle_list import VehicleListCreate, VehicleListUpdate

# Absolute path so file I/O works regardless of working directory
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "vehicles"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _format_vehicle_list(doc: dict) -> dict:
    return {
        "_id": str(doc["_id"]),
        "nom": doc["nom"],
        "image_url": doc["image_url"],
        "created_at": doc["created_at"],
    }


def create_vehicle_list(db: Database, payload: VehicleListCreate, image_file=None) -> dict:
    now = datetime.utcnow()
    image_url = None

    if image_file and image_file.filename:
        filename = f"vehicle_{ObjectId()}_{image_file.filename}"
        filepath = UPLOAD_DIR / filename
        try:
            image_file.save(str(filepath))
            image_url = f"/uploads/vehicles/{filename}"
        except Exception as e:
            raise APIException(400, f"Erreur lors du téléchargement de l'image: {str(e)}")

    document = {"nom": payload.nom, "image_url": image_url, "created_at": now}

    try:
        result = db["vehicleListe"].insert_one(document)
        document["_id"] = result.inserted_id
        return _format_vehicle_list(document)
    except DuplicateKeyError:
        raise APIException(409, "Un élément avec ce nom existe déjà.")


def get_vehicle_list_by_id(db: Database, item_id: str) -> dict | None:
    if not ObjectId.is_valid(item_id):
        return None
    document = db["vehicleListe"].find_one({"_id": ObjectId(item_id)})
    return _format_vehicle_list(document) if document else None


def list_vehicle_list(db: Database, page: int = 1, size: int = 10) -> dict:
    skip = max(page - 1, 0) * size
    items = [_format_vehicle_list(doc) for doc in db["vehicleListe"].find({}).skip(skip).limit(size)]
    total = db["vehicleListe"].count_documents({})
    return {"items": items, "total": total, "page": page, "size": size}


def update_vehicle_list(db: Database, item_id: str, payload: VehicleListUpdate, image_file=None) -> dict:
    if not ObjectId.is_valid(item_id):
        raise APIException(404, "Élément introuvable.")

    existing = db["vehicleListe"].find_one({"_id": ObjectId(item_id)})
    if not existing:
        raise APIException(404, "Élément introuvable.")

    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}

    if image_file and image_file.filename:
        if existing.get("image_url"):
            old_filename = existing["image_url"].split("/")[-1]
            old_filepath = UPLOAD_DIR / old_filename
            try:
                if old_filepath.exists():
                    old_filepath.unlink()
            except Exception:
                pass

        try:
            filename = f"vehicle_{ObjectId()}_{image_file.filename}"
            filepath = UPLOAD_DIR / filename
            image_file.save(str(filepath))
            update_data["image_url"] = f"/uploads/vehicles/{filename}"
        except Exception as e:
            raise APIException(400, f"Erreur lors du téléchargement de l'image: {str(e)}")

    if not update_data and not (image_file and image_file.filename):
        raise APIException(400, "Aucune donnée à mettre à jour.")

    update_data["updated_at"] = datetime.utcnow()

    try:
        updated = db["vehicleListe"].find_one_and_update(
            {"_id": ObjectId(item_id)},
            {"$set": update_data},
            return_document=True,
        )
    except DuplicateKeyError:
        raise APIException(409, "Un élément avec ce nom existe déjà.")

    if not updated:
        raise APIException(404, "Élément introuvable.")
    return _format_vehicle_list(updated)


def delete_vehicle_list(db: Database, item_id: str) -> None:
    if not ObjectId.is_valid(item_id):
        raise APIException(404, "Élément introuvable.")

    existing = db["vehicleListe"].find_one({"_id": ObjectId(item_id)})
    if existing and existing.get("image_url"):
        old_filename = existing["image_url"].split("/")[-1]
        old_filepath = UPLOAD_DIR / old_filename
        try:
            if old_filepath.exists():
                old_filepath.unlink()
        except Exception:
            pass

    result = db["vehicleListe"].delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        raise APIException(404, "Élément introuvable.")


# Dossier de stockage des images
UPLOAD_DIR = Path("uploads/vehicles")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _format_vehicle_list(doc: dict) -> dict:
    return {
        "_id": str(doc["_id"]),
        "nom": doc["nom"],
        "image_url": doc["image_url"],
        "created_at": doc["created_at"],
    }
