from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from app.algorithms.assignment_algorithms import BalancedLoadAlgorithm, GreedyCapacityAlgorithm
from app.algorithms.capacity_optimizer import CapacityOptimizer
from app.schemas.optimization import RegionSettingsUpdateRequest
from app.services.clustering_service import ClusteringService
from app.services.optimization_settings_service import OptimizationSettingsService


def _matches(document: dict, query: dict | None) -> bool:
    if not query:
        return True
    for key, value in query.items():
        if document.get(key) != value:
            return False
    return True


class MemoryCursor(list):
    def sort(self, field: str, direction: int):
        reverse = direction < 0
        super().sort(key=lambda item: item.get(field), reverse=reverse)
        return self


class MemoryCollection:
    def __init__(self, documents: list[dict] | None = None):
        self.documents = [deepcopy(document) for document in (documents or [])]
        self._counter = len(self.documents)

    def find_one(self, query: dict | None = None, sort: list[tuple[str, int]] | None = None):
        matches = [deepcopy(doc) for doc in self.documents if _matches(doc, query)]
        if not matches:
            return None
        if sort:
            for field, direction in reversed(sort):
                matches.sort(key=lambda item: item.get(field), reverse=direction < 0)
        return matches[0]

    def find(self, query: dict | None = None):
        return MemoryCursor([deepcopy(doc) for doc in self.documents if _matches(doc, query)])

    def insert_one(self, document: dict):
        self._counter += 1
        stored_document = deepcopy(document)
        stored_document.setdefault("_id", f"doc-{self._counter}")
        self.documents.append(stored_document)
        return SimpleNamespace(inserted_id=stored_document["_id"])

    def insert_many(self, documents: list[dict]):
        inserted_ids = []
        for document in documents:
            inserted_ids.append(self.insert_one(document).inserted_id)
        return SimpleNamespace(inserted_ids=inserted_ids)

    def update_one(self, query: dict, update: dict):
        for document in self.documents:
            if _matches(document, query):
                if "$set" in update:
                    document.update(deepcopy(update["$set"]))
                return SimpleNamespace(modified_count=1)
        return SimpleNamespace(modified_count=0)

    def update_many(self, query: dict, update: dict):
        modified_count = 0
        for document in self.documents:
            if _matches(document, query):
                if "$set" in update:
                    document.update(deepcopy(update["$set"]))
                modified_count += 1
        return SimpleNamespace(modified_count=modified_count)

    def count_documents(self, query: dict):
        return len([doc for doc in self.documents if _matches(doc, query)])

    def create_index(self, *args, **kwargs):
        return None


class FakeDatabase:
    def __init__(self, *, region_settings=None, region_geometry=None, algorithm_settings=None):
        self.region_settings = MemoryCollection(region_settings)
        self.region_geometry = MemoryCollection(region_geometry)
        self.algorithm_settings = MemoryCollection(algorithm_settings)


def test_capacity_optimizer_defaults_to_greedy_without_settings():
    db = FakeDatabase()
    optimizer = CapacityOptimizer(db)

    algorithm = optimizer._resolve_algorithm()

    assert isinstance(algorithm, GreedyCapacityAlgorithm)


def test_region_settings_request_allows_empty_cluster_values():
    for value in (None, ""):
        payload = RegionSettingsUpdateRequest(n_clusters=value, mode="fixe")
        assert payload.n_clusters is None


def test_capacity_optimizer_uses_active_balanced_algorithm():
    db = FakeDatabase(
        algorithm_settings=[
            {"algorithm_name": "greedy_capacity", "is_active": False, "parameters": {}, "updated_at": 1},
            {"algorithm_name": "balanced_load", "is_active": True, "parameters": {}, "updated_at": 1},
        ]
    )
    optimizer = CapacityOptimizer(db)

    algorithm = optimizer._resolve_algorithm()

    assert isinstance(algorithm, BalancedLoadAlgorithm)


def test_region_settings_auto_mode_uses_driver_count():
    db = FakeDatabase(region_settings=[{"n_clusters": 5, "mode": "auto", "updated_at": 1}])

    clustering_service = ClusteringService(db=db, driver_count=2)

    assert clustering_service.n_clusters == 2


def test_cluster_deliveries_persists_region_geometry():
    db = FakeDatabase(region_settings=[{"n_clusters": 2, "mode": "fixe", "updated_at": 1}])
    clustering_service = ClusteringService(db=db, driver_count=4)

    deliveries = [
        {
            "id": "d1",
            "pickup_address_lat": 0.0,
            "pickup_address_lng": 0.0,
            "dropoff_address_lat": 0.0,
            "dropoff_address_lng": 0.1,
        },
        {
            "id": "d2",
            "pickup_address_lat": 0.1,
            "pickup_address_lng": 0.0,
            "dropoff_address_lat": 0.1,
            "dropoff_address_lng": 0.1,
        },
        {
            "id": "d3",
            "pickup_address_lat": 10.0,
            "pickup_address_lng": 10.0,
            "dropoff_address_lat": 10.1,
            "dropoff_address_lng": 10.1,
        },
        {
            "id": "d4",
            "pickup_address_lat": 10.2,
            "pickup_address_lng": 10.0,
            "dropoff_address_lat": 10.2,
            "dropoff_address_lng": 10.1,
        },
    ]

    regions = clustering_service.cluster_deliveries(deliveries)

    assert len(regions) == 2
    assert db.region_geometry.count_documents({}) == 2

    persisted_geometry = list(db.region_geometry.find().sort("region_id", 1))
    assert all(geometry["radius_km"] >= 0 for geometry in persisted_geometry)
    assert all("center_lat" in geometry and "center_lng" in geometry for geometry in persisted_geometry)