from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest
from flask import Flask

import app.dependencies as dependencies_module
import app.routers.missions as missions_module
from app.algorithms.route_strategies import respects_pickup_before_delivery


@pytest.fixture(autouse=True)
def _authenticated_request(monkeypatch):
    """
    missions_bp routes now require @require_auth (see app/routers/missions.py).
    Route functions here are called directly rather than through a real HTTP
    request, so there's no JWT to decode — stub get_current_user() the same
    way require_auth's decorated() looks it up (as a module-level name on
    app.dependencies, resolved at call time) to simulate an already-logged-in
    user without touching the DB.
    """
    monkeypatch.setattr(
        dependencies_module,
        "get_current_user",
        lambda: ({"_id": "admin-1", "role": "admin", "is_active": True}, None),
    )


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = list(documents or [])
        self._counter = len(self.documents)

    def find(self, query=None):
        query = query or {}
        return [doc for doc in self.documents if self._matches(doc, query)]

    def find_one(self, query=None, projection=None, sort=None):
        query = query or {}
        matches = [doc for doc in self.documents if self._matches(doc, query)]
        if sort:
            for field, direction in reversed(sort):
                matches.sort(key=lambda item: item.get(field), reverse=direction < 0)
        return matches[0] if matches else None

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
            elif doc.get(key) != expected:
                return False
        return True


class FakeDatabase:
    def __init__(self):
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        self.deliveries = FakeCollection([
            {
                "_id": f"del-{i}",
                "status": "pending",
                "scheduled_at": today,
                "weight_kg": 50,
                "pickup_address": f"pickup-{i}",
                "pickup_address_lat": 0.0 + i,
                "pickup_address_lng": 0.0,
                "dropoff_address": f"dropoff-{i}",
                "dropoff_address_lat": 0.0 + i,
                "dropoff_address_lng": 1.0,
            }
            for i in range(4)
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


def _call_test_generate(app, body):
    with app.test_request_context(
        "/api/missions/test-generate", method="POST", json=body
    ):
        response, status_code = missions_module.test_generate_missions()
        return status_code, response.get_json()


def _call_generate(app, body):
    with app.test_request_context(
        "/api/missions/generate", method="POST", json=body
    ):
        response, status_code = missions_module.generate_missions()
        return status_code, response.get_json()


def _call_assign(app, body):
    with app.test_request_context(
        "/api/missions/assign", method="POST", json=body
    ):
        response, status_code = missions_module.assign_deliveries()
        return status_code, response.get_json()


def test_test_generate_missions_route_with_each_route_strategy(monkeypatch):
    import app.services.osm_routing_service as osm_routing_module

    monkeypatch.setattr(
        osm_routing_module.OSMRoutingService,
        "calculate_route",
        lambda self, coordinates: {"distance": 12.4, "duration": 1488, "geometry": "abc"},
    )

    app = Flask(__name__)
    app.mongodb = FakeDatabase()

    for strategy_name in ("clarke_wright", "ortools_cvrp"):
        status_code, payload = _call_test_generate(
            app, {"route_strategy": strategy_name, "route_strategy_parameters": {"time_limit_seconds": 2}}
        )

        assert status_code == 200
        assert payload["success"] is True
        assert payload["route_strategy_used"] == strategy_name
        assert payload["route_optimization_time_ms"] >= 0
        assert payload["total_assignments"] >= 1
        assert payload["total_distance"] > 0
        assert payload["simulation_run_id"]
        for assignment in payload["assignments"]:
            assert assignment["route_distance"] > 0
            steps = assignment.get("deliveries_order")
            if steps:
                assert respects_pickup_before_delivery(steps)

    # A test-generate simulation must never add/modify anything in `missions` or
    # mark deliveries as assigned in `deliveries` — only mission_simulations grows.
    assert app.mongodb.missions.documents == []
    assert len(app.mongodb.mission_simulations.documents) == 2  # one run per strategy above
    for delivery in app.mongodb.deliveries.documents:
        assert delivery["status"] == "pending"
        assert "driver_id" not in delivery


def test_generate_missions_route_persists_to_missions_definitively(monkeypatch):
    import app.services.osm_routing_service as osm_routing_module

    monkeypatch.setattr(
        osm_routing_module.OSMRoutingService,
        "calculate_route",
        lambda self, coordinates: {"distance": 12.4, "duration": 1488, "geometry": "abc"},
    )

    app = Flask(__name__)
    app.mongodb = FakeDatabase()

    status_code, payload = _call_generate(app, {})

    assert status_code == 200
    assert payload["missions"]
    assert app.mongodb.mission_simulations.documents == []
    assert len(app.mongodb.missions.documents) == len(payload["missions"])

    # Only one driver is available in this fixture, so with 4 geographically
    # separate deliveries not every delivery necessarily gets a mission — but
    # every delivery covered by a saved mission must be marked "assigned", and
    # every delivery NOT covered must show up in unassigned_delivery_ids (not
    # silently dropped).
    assigned_ids = {did for m in payload["missions"] for did in m["delivery_ids"]}
    assert assigned_ids
    for delivery in app.mongodb.deliveries.documents:
        if str(delivery["_id"]) in assigned_ids:
            assert delivery["status"] == "assigned"
        else:
            assert delivery["status"] == "pending"
            assert str(delivery["_id"]) in payload["unassigned_delivery_ids"]


def test_assign_deliveries_route_computes_real_route_via_osrm(monkeypatch):
    """
    POST /api/missions/assign used to build its own mission dict without ever
    calling OSRM, always persisting polyline=None and a Haversine-only
    route_distance/estimated_duration — inconsistent with /generate. It now
    reuses MissionService._create_mission_from_assignment/_save_mission, the
    same helpers /generate relies on, so both routes behave identically.
    """
    import app.services.osm_routing_service as osm_routing_module

    monkeypatch.setattr(
        osm_routing_module.OSMRoutingService,
        "calculate_route",
        lambda self, coordinates: {"distance": 12.4, "duration": 1488, "geometry": "encoded-geometry"},
    )

    app = Flask(__name__)
    app.mongodb = FakeDatabase()

    status_code, payload = _call_assign(app, {})

    assert status_code == 200
    assert payload["total_assignments"] >= 1
    for assignment in payload["assignments"]:
        assert assignment["polyline"] == "encoded-geometry"
        assert assignment["route_distance"] == 12.4
        assert assignment["estimated_duration"] == 1488
        assert "mission_id" in assignment

    # Saved missions must carry the OSRM-derived polyline too, not None.
    assert app.mongodb.missions.documents
    for mission in app.mongodb.missions.documents:
        assert mission["polyline"] == "encoded-geometry"
