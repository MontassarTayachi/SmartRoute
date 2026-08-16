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
        if isinstance(value, dict):
            if "$gte" in value and not (document.get(key) >= value["$gte"]):
                return False
            if "$gt" in value and not (document.get(key) > value["$gt"]):
                return False
            if "$lte" in value and not (document.get(key) <= value["$lte"]):
                return False
            if "$lt" in value and not (document.get(key) < value["$lt"]):
                return False
            continue
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

    def delete_many(self, query: dict):
        remaining = [doc for doc in self.documents if not _matches(doc, query)]
        deleted_count = len(self.documents) - len(remaining)
        self.documents = remaining
        return SimpleNamespace(deleted_count=deleted_count)

    def create_index(self, *args, **kwargs):
        return None


class FakeDatabase:
    def __init__(
        self,
        *,
        region_settings=None,
        region_geometry=None,
        algorithm_settings=None,
        route_strategy_settings=None,
        missions=None,
    ):
        self.region_settings = MemoryCollection(region_settings)
        self.region_geometry = MemoryCollection(region_geometry)
        self.algorithm_settings = MemoryCollection(algorithm_settings)
        self.route_strategy_settings = MemoryCollection(route_strategy_settings)
        self.missions = MemoryCollection(missions)


def test_capacity_optimizer_defaults_to_greedy_without_settings():
    db = FakeDatabase()
    optimizer = CapacityOptimizer(db)

    algorithm = optimizer._resolve_algorithm()

    assert isinstance(algorithm, GreedyCapacityAlgorithm)


def test_resolve_route_strategy_defaults_to_savings_without_settings():
    from app.algorithms.route_strategies import SavingsRouteStrategy

    db = FakeDatabase()
    service = OptimizationSettingsService(db)

    strategy = service.resolve_route_strategy()

    assert isinstance(strategy, SavingsRouteStrategy)


def test_resolve_route_strategy_defaults_to_savings_on_unknown_name():
    from app.algorithms.route_strategies import SavingsRouteStrategy

    db = FakeDatabase(
        route_strategy_settings=[
            {"strategy_name": "made_up", "is_active": True, "parameters": {}, "updated_at": 1},
        ]
    )
    service = OptimizationSettingsService(db)

    strategy = service.resolve_route_strategy()

    assert isinstance(strategy, SavingsRouteStrategy)


def test_resolve_route_strategy_uses_active_ortools_strategy():
    from app.algorithms.ortools_strategy import ORToolsRouteStrategy

    db = FakeDatabase(
        route_strategy_settings=[
            {"strategy_name": "clarke_wright", "is_active": False, "parameters": {}, "updated_at": 1},
            {
                "strategy_name": "ortools_cvrp",
                "is_active": True,
                "parameters": {"time_limit_seconds": 2},
                "updated_at": 1,
            },
        ]
    )
    service = OptimizationSettingsService(db)

    strategy = service.resolve_route_strategy()

    assert isinstance(strategy, ORToolsRouteStrategy)
    assert strategy.parameters["time_limit_seconds"] == 2


def test_activate_route_strategy_deactivates_others():
    db = FakeDatabase(
        route_strategy_settings=[
            {"_id": "rs1", "strategy_name": "clarke_wright", "is_active": True, "parameters": {}, "updated_at": 1},
            {"_id": "rs2", "strategy_name": "ortools_cvrp", "is_active": False, "parameters": {}, "updated_at": 1},
        ]
    )
    service = OptimizationSettingsService(db)

    updated = service.activate_route_strategy(
        strategy_name="ortools_cvrp", parameters={"time_limit_seconds": 10}, updated_by=None
    )

    assert updated["is_active"] is True
    assert updated["parameters"] == {"time_limit_seconds": 10}
    active = [doc for doc in db.route_strategy_settings.documents if doc["is_active"]]
    assert [doc["strategy_name"] for doc in active] == ["ortools_cvrp"]


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


def test_list_region_geometry_filters_regions_outside_current_settings():
    db = FakeDatabase(
        region_settings=[{"n_clusters": 2, "mode": "fixe", "updated_at": 1}],
        region_geometry=[
            {"region_id": 0, "center_lat": 1.0, "center_lng": 2.0, "radius_km": 3.0},
            {"region_id": 3, "center_lat": 4.0, "center_lng": 5.0, "radius_km": 6.0},
            {"region_id": 4, "center_lat": 7.0, "center_lng": 8.0, "radius_km": 9.0},
        ],
    )
    service = OptimizationSettingsService(db)

    geometries = service.list_region_geometry()

    assert [geometry["region_id"] for geometry in geometries] == [0]


def test_update_region_settings_prunes_regions_and_missions_beyond_new_count():
    db = FakeDatabase(
        region_settings=[{"n_clusters": 5, "mode": "fixe", "updated_at": 1}],
        region_geometry=[
            {"region_id": 0, "center_lat": 1.0, "center_lng": 2.0, "radius_km": 3.0},
            {"region_id": 4, "center_lat": 7.0, "center_lng": 8.0, "radius_km": 9.0},
        ],
        missions=[
            {"_id": "m1", "region_id": 4},
            {"_id": "m2", "region_id": 2},
        ],
    )
    service = OptimizationSettingsService(db)

    service.update_region_settings(n_clusters=4, mode="fixe", updated_by=None)

    assert db.region_geometry.count_documents({}) == 1
    assert db.missions.find_one({"_id": "m1"})["region_id"] is None


def test_update_region_settings_auto_mode_without_value_keeps_previous_n_clusters():
    """
    RegionSettingsPanel disables the n_clusters field and sends n_clusters=None
    when mode="auto". update_region_settings used to always fall back to a
    hardcoded 5 in that case, silently discarding whatever n_clusters had been
    configured before switching to auto mode.
    """
    db = FakeDatabase(region_settings=[{"n_clusters": 12, "mode": "fixe", "updated_at": 1}])
    service = OptimizationSettingsService(db)

    updated = service.update_region_settings(n_clusters=None, mode="auto", updated_by=None)

    assert updated["n_clusters"] == 12
    assert updated["mode"] == "auto"


def test_update_region_settings_defaults_to_five_when_never_configured():
    db = FakeDatabase()
    service = OptimizationSettingsService(db)

    updated = service.update_region_settings(n_clusters=None, mode="auto", updated_by=None)

    assert updated["n_clusters"] == 5


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

    regions, deliveries_without_coordinates = clustering_service.cluster_deliveries(deliveries)

    assert len(regions) == 2
    assert deliveries_without_coordinates == []
    assert db.region_geometry.count_documents({}) == 2

    persisted_geometry = list(db.region_geometry.find().sort("region_id", 1))
    assert all(geometry["radius_km"] >= 0 for geometry in persisted_geometry)
    assert all("center_lat" in geometry and "center_lng" in geometry for geometry in persisted_geometry)


def test_cluster_deliveries_excludes_missing_coordinates_instead_of_using_origin():
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
            "pickup_address_lat": 10.0,
            "pickup_address_lng": 10.0,
            "dropoff_address_lat": 10.1,
            "dropoff_address_lng": 10.1,
        },
        {
            "id": "d3-missing",
            "pickup_address_lat": None,
            "pickup_address_lng": None,
            "dropoff_address_lat": None,
            "dropoff_address_lng": None,
        },
    ]

    regions, deliveries_without_coordinates = clustering_service.cluster_deliveries(deliveries)

    assert [d["id"] for d in deliveries_without_coordinates] == ["d3-missing"]
    clustered_ids = {d["id"] for deliveries_in_region in regions.values() for d in deliveries_in_region}
    assert clustered_ids == {"d1", "d2"}
    assert "d3-missing" not in clustered_ids