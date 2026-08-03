from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from bson import ObjectId

from app.algorithms.assignment_algorithms import (
    BalancedLoadAlgorithm,
    GreedyCapacityAlgorithm,
)
from app.core.exceptions import APIException


logger = logging.getLogger(__name__)


def _normalize_object_id(value: Any | None) -> ObjectId | None:
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    raise APIException(400, "Identifiant utilisateur invalide.")


class OptimizationSettingsService:
    """Read and write optimization settings stored in MongoDB."""

    def __init__(self, db):
        self.db = db

    def get_region_settings(self) -> dict[str, Any] | None:
        return self.db.region_settings.find_one(sort=[("updated_at", -1)])

    def update_region_settings(
        self,
        *,
        n_clusters: int | None,
        mode: str,
        updated_by: Any | None,
    ) -> dict[str, Any]:
        resolved_n_clusters = 5
        if n_clusters is not None:
            if isinstance(n_clusters, str):
                cleaned_value = n_clusters.strip()
                if cleaned_value:
                    try:
                        resolved_n_clusters = int(cleaned_value)
                    except ValueError as exc:
                        raise APIException(400, "Le nombre de regions doit être un entier valide.") from exc
                else:
                    resolved_n_clusters = 5
            else:
                resolved_n_clusters = int(n_clusters)

        if resolved_n_clusters < 1:
            raise APIException(400, "Le nombre de regions doit être supérieur à zéro.")
        if mode not in {"fixe", "auto"}:
            raise APIException(400, "Le mode de regions doit être 'fixe' ou 'auto'.")

        normalized_updated_by = _normalize_object_id(updated_by)

        now = datetime.utcnow()
        payload = {
            "n_clusters": resolved_n_clusters,
            "mode": mode,
            "updated_by": normalized_updated_by,
            "updated_at": now,
        }

        existing = self.get_region_settings()
        if existing:
            self.db.region_settings.update_one({"_id": existing["_id"]}, {"$set": payload})
            payload["_id"] = existing["_id"]
        else:
            result = self.db.region_settings.insert_one(payload)
            payload["_id"] = result.inserted_id

        # Delete region geometry entries for regions that exceed the new n_clusters
        # This ensures the map is synchronized with the new configuration
        delete_result = self.db.region_geometry.delete_many({
            "region_id": {"$gte": resolved_n_clusters}
        })
        if delete_result.deleted_count > 0:
            logger.info(f"Deleted {delete_result.deleted_count} region geometry entries exceeding new n_clusters={resolved_n_clusters}")

        # Also update missions with region_id exceeding the new n_clusters
        # Set their region_id to null to avoid referencing non-existent regions
        mission_update_result = self.db.missions.update_many(
            {"region_id": {"$gte": resolved_n_clusters}},
            {"$set": {"region_id": None}}
        )
        if mission_update_result.modified_count > 0:
            logger.info(f"Updated {mission_update_result.modified_count} missions with region_id exceeding new n_clusters={resolved_n_clusters}")

        return payload

    def save_region_geometry(
        self,
        *,
        region_id: int,
        center_lat: float,
        center_lng: float,
        radius_km: float,
    ) -> dict[str, Any]:
        now = datetime.utcnow()
        payload = {
            "region_id": region_id,
            "center_lat": center_lat,
            "center_lng": center_lng,
            "radius_km": radius_km,
            "computed_at": now,
        }

        existing = self.db.region_geometry.find_one({"region_id": region_id})
        if existing:
            self.db.region_geometry.update_one({"_id": existing["_id"]}, {"$set": payload})
            payload["_id"] = existing["_id"]
        else:
            result = self.db.region_geometry.insert_one(payload)
            payload["_id"] = result.inserted_id

        return payload

    def list_region_geometry(self) -> list[dict[str, Any]]:
        return list(self.db.region_geometry.find().sort("region_id", 1))

    def list_algorithms(self) -> list[dict[str, Any]]:
        return list(self.db.algorithm_settings.find().sort("algorithm_name", 1))

    def get_active_algorithm(self) -> dict[str, Any] | None:
        return self.db.algorithm_settings.find_one({"is_active": True})

    def activate_algorithm(
        self,
        *,
        algorithm_name: str,
        parameters: dict[str, Any] | None,
        updated_by: Any | None,
    ) -> dict[str, Any]:
        existing = self.db.algorithm_settings.find_one({"algorithm_name": algorithm_name})
        if not existing:
            raise APIException(404, f"Algorithme {algorithm_name} introuvable.")

        now = datetime.utcnow()
        normalized_updated_by = _normalize_object_id(updated_by)

        self.db.algorithm_settings.update_many({}, {"$set": {"is_active": False, "updated_at": now}})

        payload = {
            "is_active": True,
            "parameters": parameters if parameters is not None else existing.get("parameters", {}),
            "updated_by": normalized_updated_by,
            "updated_at": now,
        }
        self.db.algorithm_settings.update_one({"_id": existing["_id"]}, {"$set": payload})
        existing.update(payload)
        return existing

    def resolve_assignment_algorithm(self):
        active = self.get_active_algorithm()
        if not active:
            logger.info("No active assignment algorithm configured. Falling back to greedy.")
            return GreedyCapacityAlgorithm()

        algorithm_name = active.get("algorithm_name")
        parameters = active.get("parameters") or {}

        if algorithm_name == GreedyCapacityAlgorithm.algorithm_name:
            return GreedyCapacityAlgorithm(parameters)
        if algorithm_name == BalancedLoadAlgorithm.algorithm_name:
            return BalancedLoadAlgorithm(parameters)

        logger.warning("Unknown active algorithm %s. Falling back to greedy.", algorithm_name)
        return GreedyCapacityAlgorithm()