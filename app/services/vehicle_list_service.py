import os
from datetime import datetime
from pathlib import Path
from bson import ObjectId
from fastapi import HTTPException, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.schemas.vehicle_list import VehicleListCreate, VehicleListUpdate

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


async def create_vehicle_list(
    db: AsyncIOMotorDatabase,
    payload: VehicleListCreate,
    image_file: UploadFile | None = None,
) -> dict:
    now = datetime.utcnow()
    image_url = None

    # Traiter l'image si fournie
    if image_file:
        # Générer un nom de fichier unique
        file_ext = Path(image_file.filename).suffix
        filename = f"vehicle_{ObjectId()}_{image_file.filename}"
        filepath = UPLOAD_DIR / filename

        # Sauvegarder l'image
        try:
            content = await image_file.read()
            with open(filepath, "wb") as f:
                f.write(content)
            image_url = f"/uploads/vehicles/{filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur lors du téléchargement de l'image: {str(e)}",
            )

    document = {
        "nom": payload.nom,
        "image_url": image_url,
        "created_at": now,
    }

    try:
        result = await db["vehicleListe"].insert_one(document)
        document["_id"] = result.inserted_id
        return _format_vehicle_list(document)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un élément avec ce nom existe déjà.",
        )


async def get_vehicle_list_by_id(db: AsyncIOMotorDatabase, item_id: str) -> dict | None:
    if not ObjectId.is_valid(item_id):
        return None
    document = await db["vehicleListe"].find_one({"_id": ObjectId(item_id)})
    return _format_vehicle_list(document) if document else None


async def list_vehicle_list(
    db: AsyncIOMotorDatabase, page: int = 1, size: int = 10
) -> dict:
    skip = max(page - 1, 0) * size

    cursor = db["vehicleListe"].find({}).skip(skip).limit(size)
    items = [
        _format_vehicle_list(doc)
        for doc in await cursor.to_list(length=size)
    ]
    total = await db["vehicleListe"].count_documents({})
    return {"items": items, "total": total, "page": page, "size": size}


async def update_vehicle_list(
    db: AsyncIOMotorDatabase,
    item_id: str,
    payload: VehicleListUpdate,
    image_file: UploadFile | None = None,
) -> dict:
    if not ObjectId.is_valid(item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément introuvable.",
        )

    # Récupérer le document existant
    existing = await db["vehicleListe"].find_one({"_id": ObjectId(item_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément introuvable.",
        )

    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}

    # Traiter la nouvelle image si fournie
    if image_file:
        # Supprimer l'ancienne image si elle existe
        if existing.get("image_url"):
            old_filename = existing["image_url"].split("/")[-1]
            old_filepath = UPLOAD_DIR / old_filename
            try:
                if old_filepath.exists():
                    old_filepath.unlink()
            except Exception:
                pass

        # Sauvegarder la nouvelle image
        try:
            file_ext = Path(image_file.filename).suffix
            filename = f"vehicle_{ObjectId()}_{image_file.filename}"
            filepath = UPLOAD_DIR / filename

            content = await image_file.read()
            with open(filepath, "wb") as f:
                f.write(content)
            update_data["image_url"] = f"/uploads/vehicles/{filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur lors du téléchargement de l'image: {str(e)}",
            )

    if not update_data and not image_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucune donnée à mettre à jour.",
        )

    update_data["updated_at"] = datetime.utcnow()

    try:
        updated = await db["vehicleListe"].find_one_and_update(
            {"_id": ObjectId(item_id)},
            {"$set": update_data},
            return_document=True,
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un élément avec ce nom existe déjà.",
        )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément introuvable.",
        )
    return _format_vehicle_list(updated)


async def delete_vehicle_list(db: AsyncIOMotorDatabase, item_id: str) -> None:
    if not ObjectId.is_valid(item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément introuvable.",
        )

    # Récupérer le document pour supprimer l'image
    existing = await db["vehicleListe"].find_one({"_id": ObjectId(item_id)})
    if existing and existing.get("image_url"):
        old_filename = existing["image_url"].split("/")[-1]
        old_filepath = UPLOAD_DIR / old_filename
        try:
            if old_filepath.exists():
                old_filepath.unlink()
        except Exception:
            pass

    result = await db["vehicleListe"].delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément introuvable.",
        )
