from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from app.services.mission_service import MissionService


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = list(documents or [])
        self._counter = len(self.documents)

    def find(self, query=None):
        query = query or {}
        matches = []
        for doc in self.documents:
            if self._matches(doc, query):
                matches.append(doc)
        return list(matches)

    def find_one(self, query=None, projection=None, sort=None):
        query = query or {}
        matches = [doc for doc in self.documents if self._matches(doc, query)]
        if sort:
            for field, direction in reversed(sort):
                matches.sort(key=lambda item: item.get(field), reverse=direction < 0)
        if matches:
            return matches[0]
        return None

    def insert_one(self, document):
        self._counter += 1
        stored = dict(document)
        stored.setdefault("_id", self._counter)
        self.documents.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    def update_one(self, query, update):
        for doc in self.documents:
            if self._matches(doc, query):
                if "$set" in update:
                    doc.update(update["$set"])
                return SimpleNamespace(modified_count=1)
        return SimpleNamespace(modified_count=0)

    @staticmethod
    def _matches(doc, query):
        if not query:
            return True
        for key, expected in query.items():
            if key == "$in":
                continue
            if isinstance(expected, dict):
                for sub_key, sub_value in expected.items():
                    if sub_key == "$gte":
                        if doc.get(key) < sub_value:
                            return False
                    elif sub_key == "$lt":
                        if doc.get(key) >= sub_value:
                            return False
                    elif sub_key == "$in":
                        if doc.get(key) not in sub_value:
                            return False
                    else:
                        if doc.get(key, {}).get(sub_key) != sub_value:
                            return False
            elif isinstance(expected, list):
                if doc.get(key) not in expected:
                    return False
            elif doc.get(key) != expected:
                return False
        return True


class FakeDatabase:
    def __init__(self):
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        self.deliveries = FakeCollection([
            {
                "_id": "del-1",
                "status": "pending",
                "scheduled_at": today,
                "weight_kg": 100,
                "pickup_address_lat": 0.0,
                "pickup_address_lng": 0.0,
                "dropoff_address_lat": 0.0,
                "dropoff_address_lng": 0.1,
            }
        ])
        self.drivers = FakeCollection([
            {
                "_id": "drv-1",
                "availability": "available",
                "assigned_vehicle_id": "veh-1",
                "current_lat": 0.0,
                "current_lng": 0.0,
            }
        ])
        self.vehicles = FakeCollection([
            {"_id": "veh-1", "status": "available", "capacity_kg": 1000}
        ])
        self.missions = FakeCollection([])
        self.mission_simulations = FakeCollection([])
        self.region_settings = FakeCollection([])
        self.region_geometry = FakeCollection([])
        self.algorithm_settings = FakeCollection([])
        self.route_strategy_settings = FakeCollection([])


def test_generate_missions_marks_deliveries_as_assigned(monkeypatch):
    db = FakeDatabase()
    service = MissionService(db)

    monkeypatch.setattr(
        service.route_optimizer,
        "optimize_mission_route",
        lambda deliveries, strategy=None: {
            "steps": [
                {
                    "delivery_id": deliveries[0]["_id"],
                    "step_type": "pickup",
                    "address": "A",
                    "lat": 0.0,
                    "lng": 0.0,
                    "order": 1,
                },
                {
                    "delivery_id": deliveries[0]["_id"],
                    "step_type": "delivery",
                    "address": "B",
                    "lat": 0.1,
                    "lng": 0.1,
                    "order": 2,
                },
            ],
            "total_distance": 1.0,
            "estimated_duration": 60,
        },
    )
    monkeypatch.setattr(service.osm_routing_service, "calculate_route", lambda coordinates: {"distance": 1.0, "duration": 60, "geometry": "abc"})

    result = service.generate_missions_for_date()

    assert result["missions"]
    assert result["unassigned_delivery_ids"] == []
    delivery = db.deliveries.find_one({"_id": "del-1"})
    assert delivery["status"] == "assigned"
    assert delivery["driver_id"] == "drv-1"
    assert delivery["vehicle_id"] == "veh-1"


def test_generate_missions_reports_delivery_without_coordinates_as_unassigned(monkeypatch):
    db = FakeDatabase()
    db.deliveries.documents.append({
        "_id": "del-2",
        "status": "pending",
        "scheduled_at": db.deliveries.documents[0]["scheduled_at"],
        "weight_kg": 50,
        "pickup_address_lat": None,
        "pickup_address_lng": None,
        "dropoff_address_lat": None,
        "dropoff_address_lng": None,
    })
    service = MissionService(db)

    monkeypatch.setattr(
        service.route_optimizer,
        "optimize_mission_route",
        lambda deliveries, strategy=None: {
            "steps": [
                {
                    "delivery_id": deliveries[0]["_id"],
                    "step_type": "pickup",
                    "address": "A",
                    "lat": 0.0,
                    "lng": 0.0,
                    "order": 1,
                },
                {
                    "delivery_id": deliveries[0]["_id"],
                    "step_type": "delivery",
                    "address": "B",
                    "lat": 0.1,
                    "lng": 0.1,
                    "order": 2,
                },
            ],
            "total_distance": 1.0,
            "estimated_duration": 60,
        },
    )
    monkeypatch.setattr(service.osm_routing_service, "calculate_route", lambda coordinates: {"distance": 1.0, "duration": 60, "geometry": "abc"})

    result = service.generate_missions_for_date()

    assert result["unassigned_delivery_ids"] == ["del-2"]
    delivery = db.deliveries.find_one({"_id": "del-2"})
    assert delivery["status"] == "pending"


def _stub_route_optimizer(service, monkeypatch):
    monkeypatch.setattr(
        service.route_optimizer,
        "optimize_mission_route",
        lambda deliveries, strategy=None: {
            "steps": [
                {
                    "delivery_id": deliveries[0]["_id"],
                    "step_type": "pickup",
                    "address": "A",
                    "lat": 0.0,
                    "lng": 0.0,
                    "order": 1,
                },
                {
                    "delivery_id": deliveries[0]["_id"],
                    "step_type": "delivery",
                    "address": "B",
                    "lat": 0.1,
                    "lng": 0.1,
                    "order": 2,
                },
            ],
            "total_distance": 1.0,
            "estimated_duration": 60,
        },
    )
    monkeypatch.setattr(
        service.osm_routing_service,
        "calculate_route",
        lambda coordinates: {"distance": 1.0, "duration": 60, "geometry": "abc"},
    )


def test_simulate_missions_for_date_never_touches_missions_or_deliveries(monkeypatch):
    db = FakeDatabase()
    service = MissionService(db)
    _stub_route_optimizer(service, monkeypatch)

    result = service.simulate_missions_for_date()

    assert result["missions"]
    assert result["unassigned_delivery_ids"] == []
    assert result["simulation_run_id"]

    # Nothing added to the real `missions` collection...
    assert db.missions.documents == []
    # ...and the simulated missions landed in mission_simulations instead, tagged
    # with the simulation_run_id.
    assert len(db.mission_simulations.documents) == 1
    assert db.mission_simulations.documents[0]["simulation_run_id"] == result["simulation_run_id"]

    # ...and the delivery was NOT marked as assigned (no side effect on `deliveries`).
    delivery = db.deliveries.find_one({"_id": "del-1"})
    assert delivery["status"] == "pending"
    assert "driver_id" not in delivery


def test_simulate_and_generate_share_the_same_draft_builder(monkeypatch):
    db = FakeDatabase()
    service = MissionService(db)
    _stub_route_optimizer(service, monkeypatch)

    simulate_result = service.simulate_missions_for_date()
    generate_result = service.generate_missions_for_date()

    assert simulate_result["missions"][0]["route_distance"] == generate_result["missions"][0]["route_distance"]
    assert simulate_result["missions"][0]["deliveries_order"] == generate_result["missions"][0]["deliveries_order"]
    # generate persisted for real, simulate did not:
    assert len(db.missions.documents) == 1
    assert len(db.mission_simulations.documents) == 1
