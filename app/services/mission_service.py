import logging
import time
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from bson import ObjectId

from app.algorithms.capacity_optimizer import CapacityOptimizer
from app.algorithms.route_strategies import RouteOptimizationStrategy
from app.models.mission import Mission, MissionStep, MissionStatus
from app.services.clustering_service import ClusteringService
from app.services.driver_assignment_service import DriverAssignmentService
from app.services.osm_routing_service import OSMRoutingService
from app.services.route_optimizer import RouteOptimizerService

logger = logging.getLogger(__name__)


def _serialize_mission(mission: dict) -> dict:
    """Convert ObjectId fields to strings in a mission dict."""
    m = mission.copy()
    if "_id" in m:
        m["_id"] = str(m["_id"])
    if "driver_id" in m:
        m["driver_id"] = str(m["driver_id"])
    if "vehicle_id" in m:
        m["vehicle_id"] = str(m["vehicle_id"])
    if "delivery_ids" in m:
        m["delivery_ids"] = [str(did) for did in m["delivery_ids"]]
    if "deliveries_order" in m:
        for step in m["deliveries_order"]:
            if "delivery_id" in step:
                step["delivery_id"] = str(step["delivery_id"])
    # Serialize driver and vehicle objects if present
    if "driver" in m and m["driver"]:
        driver = m["driver"].copy()
        if "_id" in driver:
            driver["_id"] = str(driver["_id"])
        if "assigned_vehicle_id" in driver and driver["assigned_vehicle_id"]:
            driver["assigned_vehicle_id"] = str(driver["assigned_vehicle_id"])
        if "login_user_id" in driver and driver["login_user_id"]:
            driver["login_user_id"] = str(driver["login_user_id"])
        m["driver"] = driver
    if "vehicle" in m and m["vehicle"]:
        vehicle = m["vehicle"].copy()
        if "_id" in vehicle:
            vehicle["_id"] = str(vehicle["_id"])
        if "vehicle_list_id" in vehicle and vehicle["vehicle_list_id"]:
            vehicle["vehicle_list_id"] = str(vehicle["vehicle_list_id"])
        m["vehicle"] = vehicle
    return m


class MissionService:
    """Service for generating and managing delivery missions."""

    # Simulation runs (POST /api/missions/test-generate) are persisted here instead
    # of `missions`, so a test run never adds or modifies anything in the real
    # `missions` collection (and never touches `deliveries` either — see
    # _save_mission_simulation). See app/db/init_db.py for the collection's schema.
    MISSION_SIMULATIONS_COLLECTION = "mission_simulations"

    def __init__(self, db):
        self.db = db
        self.clustering_service = None
        self.driver_assignment_service = DriverAssignmentService()
        self.route_optimizer = RouteOptimizerService(self.db)
        self.capacity_optimizer = CapacityOptimizer(self.db)
        self.osm_routing_service = OSMRoutingService()

    def generate_missions_for_date(self, target_date: datetime | None = None) -> dict[str, Any]:
        """
        Run the full mission generation pipeline for a given date and persist the
        result definitively to `missions` (marking the covered deliveries as
        `assigned`). Shares _build_mission_drafts with simulate_missions_for_date
        so both endpoints run the exact same generation logic and only differ in
        where/whether the result is persisted.

        Returns:
            {"missions": [...saved mission dicts...], "unassigned_delivery_ids": [...]}
            NOTE: this is a breaking change to the response shape of POST /api/missions/generate,
            which used to return a bare list of missions. See app/routers/missions.py.
        """
        if target_date is None:
            target_date = datetime.utcnow()

        logger.info(f"Starting mission generation for date: {target_date.date()}")

        build_result = self._build_mission_drafts(target_date)
        deliveries = build_result["deliveries"]
        mission_drafts = build_result["mission_drafts"]

        # Computed from the built drafts (not from what _save_mission actually
        # manages to persist) to match this method's pre-existing behavior: a
        # delivery counts as "assigned" as soon as a mission was built for it.
        assigned_delivery_ids = {
            delivery_id for mission in mission_drafts for delivery_id in mission["delivery_ids"]
        }

        saved_missions = []
        for mission_dict in mission_drafts:
            saved = self._save_mission(mission_dict)
            if saved:
                saved_missions.append(saved)

        logger.info(f"Generated and saved {len(saved_missions)} missions")
        return {
            "missions": saved_missions,
            "unassigned_delivery_ids": self._compute_unassigned_delivery_ids(
                deliveries, assigned_delivery_ids
            ),
        }

    def simulate_missions_for_date(
        self,
        target_date: datetime | None = None,
        *,
        route_strategy: RouteOptimizationStrategy | None = None,
    ) -> dict[str, Any]:
        """
        Run the exact same generation pipeline as generate_missions_for_date (via
        _build_mission_drafts), but persist the result to
        `MISSION_SIMULATIONS_COLLECTION` instead of `missions`, and never mark
        deliveries as assigned. Used by POST /api/missions/test-generate so an
        admin can preview/compare route strategies on real data with zero side
        effect on `missions` or `deliveries`.

        Returns:
            {
                "missions": [...simulated mission dicts, saved to the temp collection...],
                "unassigned_delivery_ids": [...],
                "total_deliveries": int,
                "route_strategy_used": str | None,
                "route_optimization_time_ms": float,
                "simulation_run_id": str,
                "stop_reason": "no_deliveries" | "no_drivers" | "no_vehicles" | None,
            }
        """
        if target_date is None:
            target_date = datetime.utcnow()

        logger.info(f"Starting mission simulation for date: {target_date.date()}")

        build_result = self._build_mission_drafts(target_date, route_strategy=route_strategy)
        deliveries = build_result["deliveries"]
        mission_drafts = build_result["mission_drafts"]

        assigned_delivery_ids = {
            delivery_id for mission in mission_drafts for delivery_id in mission["delivery_ids"]
        }

        simulation_run_id = str(uuid4())
        simulated_missions = []
        for mission_dict in mission_drafts:
            saved = self._save_mission_simulation(mission_dict, simulation_run_id)
            if saved:
                simulated_missions.append(saved)

        logger.info(
            "Simulated %d missions for run %s in '%s' — missions/deliveries untouched",
            len(simulated_missions),
            simulation_run_id,
            self.MISSION_SIMULATIONS_COLLECTION,
        )
        return {
            "missions": simulated_missions,
            "unassigned_delivery_ids": self._compute_unassigned_delivery_ids(
                deliveries, assigned_delivery_ids
            ),
            "total_deliveries": len(deliveries),
            "route_strategy_used": build_result["route_strategy_used"],
            "route_optimization_time_ms": build_result["route_optimization_time_ms"],
            "simulation_run_id": simulation_run_id,
            "stop_reason": build_result["stop_reason"],
        }

    def _build_mission_drafts(
        self,
        target_date: datetime,
        *,
        route_strategy: RouteOptimizationStrategy | None = None,
    ) -> dict[str, Any]:
        """
        Shared generation pipeline for generate_missions_for_date and
        simulate_missions_for_date: fetch deliveries/drivers/vehicles, cluster,
        assign drivers to regions, distribute deliveries by capacity, and build one
        mission dict per assignment (route ordering via the resolved/forced
        strategy + a real OSRM route, through _create_mission_from_assignment).

        Persists nothing and never touches `deliveries` or `missions` — callers
        decide where (or whether) to persist the resulting drafts.

        Returns:
            {
                "deliveries": [...all deliveries fetched for target_date...],
                "mission_drafts": [...unsaved mission dicts...],
                "route_strategy_used": str | None,
                "route_optimization_time_ms": float,
                "stop_reason": "no_deliveries" | "no_drivers" | "no_vehicles" | None,
            }
        """
        deliveries = self._get_deliveries_for_date(target_date)
        if not deliveries:
            logger.warning(f"No deliveries found for date {target_date.date()}")
            return {
                "deliveries": [],
                "mission_drafts": [],
                "route_strategy_used": None,
                "route_optimization_time_ms": 0.0,
                "stop_reason": "no_deliveries",
            }

        drivers = self._get_available_drivers()
        vehicles = self._get_available_vehicles()
        if not drivers:
            logger.warning("No available drivers found")
            return {
                "deliveries": deliveries,
                "mission_drafts": [],
                "route_strategy_used": None,
                "route_optimization_time_ms": 0.0,
                "stop_reason": "no_drivers",
            }
        if not vehicles:
            logger.warning("No available vehicles found")
            return {
                "deliveries": deliveries,
                "mission_drafts": [],
                "route_strategy_used": None,
                "route_optimization_time_ms": 0.0,
                "stop_reason": "no_vehicles",
            }

        self.clustering_service = ClusteringService(db=self.db, driver_count=len(drivers))

        # deliveries_without_coordinates are excluded from region_deliveries by
        # ClusteringService; they simply never enter assigned_delivery_ids
        # downstream and therefore end up counted as unassigned by the caller.
        region_deliveries, _deliveries_without_coordinates = self.clustering_service.cluster_deliveries(deliveries)
        region_centers = self.clustering_service.get_region_centers()
        region_drivers = self.driver_assignment_service.assign_drivers_to_regions(drivers, region_centers)
        # See redistribute_orphaned_region_deliveries: with more regions than
        # drivers, some regions get no driver — fold their deliveries into the
        # nearest served region instead of dropping them.
        region_deliveries = self.driver_assignment_service.redistribute_orphaned_region_deliveries(
            region_deliveries, region_drivers, region_centers
        )

        resolved_strategy = route_strategy or self.route_optimizer.resolve_strategy()

        mission_drafts = []
        route_optimization_time_ms = 0.0
        for region_id, deliveries_in_region in region_deliveries.items():
            drivers_in_region = region_drivers.get(region_id, [])
            if not drivers_in_region:
                continue

            assignments = self.capacity_optimizer.distribute_deliveries_by_region(
                deliveries_in_region, drivers_in_region, vehicles
            )

            for assignment in assignments:
                # Timed as a whole (route ordering + real OSRM lookup) since both
                # now go through the same _create_mission_from_assignment call for
                # generate and test-generate alike.
                build_start = time.perf_counter()
                mission = self._create_mission_from_assignment(
                    assignment, region_id, target_date, route_strategy=resolved_strategy
                )
                route_optimization_time_ms += (time.perf_counter() - build_start) * 1000
                if mission:
                    mission_drafts.append(mission)

        return {
            "deliveries": deliveries,
            "mission_drafts": mission_drafts,
            "route_strategy_used": resolved_strategy.strategy_name,
            "route_optimization_time_ms": route_optimization_time_ms,
            "stop_reason": None,
        }

    @staticmethod
    def _delivery_ids(deliveries: list[dict[str, Any]]) -> list[str]:
        return [str(d.get("_id", d.get("id"))) for d in deliveries]

    @classmethod
    def _compute_unassigned_delivery_ids(
        cls,
        deliveries: list[dict[str, Any]],
        assigned_delivery_ids: set[Any],
    ) -> list[str]:
        """
        Deliveries selected for the run that ended up covered by no saved mission —
        includes deliveries excluded upstream by ClusteringService for missing
        coordinates, since those never make it into assigned_delivery_ids either.
        """
        all_ids = set(cls._delivery_ids(deliveries))
        assigned_ids = {str(did) for did in assigned_delivery_ids}
        return sorted(all_ids - assigned_ids)

    def _get_deliveries_for_date(self, target_date: datetime) -> list[dict[str, Any]]:
        start_of_day = datetime(target_date.year, target_date.month, target_date.day)
        end_of_day = start_of_day + timedelta(days=1)
        return list(self.db.deliveries.find({
            "scheduled_at": {"$gte": start_of_day, "$lt": end_of_day},
            "status": "pending",
        }))

    def _get_available_drivers(self) -> list[dict[str, Any]]:
        return list(self.db.drivers.find({"availability": "available"}))

    def _get_available_vehicles(self) -> list[dict[str, Any]]:
        return list(self.db.vehicles.find({"status": "available"}))

    def _create_mission_from_assignment(
        self,
        assignment: dict[str, Any],
        region_id: int,
        target_date: datetime,
        *,
        route_strategy: RouteOptimizationStrategy | None = None,
    ) -> dict[str, Any] | None:
        driver_id = assignment["driver_id"]
        vehicle_id = assignment["vehicle_id"]
        deliveries = assignment["deliveries"]

        if not deliveries:
            return None

        route_result = self.route_optimizer.optimize_mission_route(deliveries, strategy=route_strategy)

        driver = self.db.drivers.find_one({"_id": driver_id}) or self.db.drivers.find_one({"id": driver_id})
        start_location = None
        if driver:
            start_location = (
                driver.get("current_lat", deliveries[0].get("pickup_address_lat")),
                driver.get("current_lng", deliveries[0].get("pickup_address_lng")),
            )

        # Refine the optimizer's Haversine-based estimate with a real OSRM route
        # (falls back to Haversine internally if OSRM is unavailable). This is what
        # makes route_distance/route_duration/polyline authoritative here. NOTE:
        # POST /api/missions/assign (app/routers/missions.py) does NOT call OSM and
        # persists the optimizer's raw estimate with polyline=None instead — a known,
        # pre-existing inconsistency between the two mission-creation paths, not
        # changed as part of this refactor pending explicit validation.
        coordinates = [(step["lat"], step["lng"]) for step in route_result["steps"]]
        osm_route = self.osm_routing_service.calculate_route(coordinates)

        mission_steps = [
            MissionStep(
                delivery_id=step["delivery_id"],
                step_type=step["step_type"],
                address=step["address"],
                lat=step["lat"],
                lng=step["lng"],
                order=step["order"],
                is_done=False,
            )
            for step in route_result["steps"]
        ]

        mission = Mission(
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            region_id=region_id,
            deliveries=[d.get("_id", d.get("id")) for d in deliveries],
            deliveries_order=mission_steps,
            total_weight=assignment["total_weight"],
            route_distance=osm_route["distance"],
            route_duration=osm_route["duration"],
            status=MissionStatus.planned,
            polyline=osm_route["geometry"],
            scheduled_date=target_date,
        )

        return {
            "driver_id": mission.driver_id,
            "vehicle_id": mission.vehicle_id,
            "region_id": mission.region_id,
            "delivery_ids": mission.deliveries,
            "deliveries_order": [
                {
                    "delivery_id": step.delivery_id,
                    "step_type": step.step_type,
                    "address": step.address,
                    "lat": step.lat,
                    "lng": step.lng,
                    "order": step.order,
                    "is_done": step.is_done,
                }
                for step in mission.deliveries_order
            ],
            "total_weight": mission.total_weight,
            "route_distance": mission.route_distance,
            "route_duration": mission.route_duration,
            "status": mission.status.value,
            "polyline": mission.polyline,
            "created_at": mission.created_at,
            "scheduled_date": mission.scheduled_date,
            "updated_at": mission.updated_at,
        }

    def _mark_deliveries_as_assigned(self, delivery_ids: list[Any], driver_id: Any, vehicle_id: Any) -> None:
        for delivery_id in delivery_ids or []:
            normalized_delivery_id = delivery_id
            if isinstance(delivery_id, str):
                try:
                    normalized_delivery_id = ObjectId(delivery_id)
                except Exception:
                    normalized_delivery_id = delivery_id

            self.db.deliveries.update_one(
                {"_id": normalized_delivery_id},
                {
                    "$set": {
                        "status": "assigned",
                        "driver_id": driver_id,
                        "vehicle_id": vehicle_id,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

    def _save_mission(self, mission_dict: dict[str, Any]) -> dict[str, Any] | None:
        try:
            mission_dict.pop("_id", None)
            result = self.db.missions.insert_one(mission_dict)
            if result.inserted_id:
                mission_dict["_id"] = str(result.inserted_id)
                self._mark_deliveries_as_assigned(
                    delivery_ids=mission_dict.get("delivery_ids", []),
                    driver_id=mission_dict.get("driver_id"),
                    vehicle_id=mission_dict.get("vehicle_id"),
                )
                logger.info(f"Saved mission {result.inserted_id}")
                return mission_dict
        except Exception as e:
            logger.error(f"Failed to save mission: {e}")
        return None

    def _save_mission_simulation(
        self, mission_dict: dict[str, Any], simulation_run_id: str
    ) -> dict[str, Any] | None:
        """
        Persist a mission draft to MISSION_SIMULATIONS_COLLECTION instead of
        `missions`. Unlike _save_mission, this never calls
        _mark_deliveries_as_assigned — a simulation run must have zero side effect
        on `missions` or `deliveries`.
        """
        try:
            mission_dict = dict(mission_dict)
            mission_dict.pop("_id", None)
            mission_dict["simulation_run_id"] = simulation_run_id
            collection = getattr(self.db, self.MISSION_SIMULATIONS_COLLECTION)
            result = collection.insert_one(mission_dict)
            if result.inserted_id:
                mission_dict["_id"] = str(result.inserted_id)
                return mission_dict
        except Exception as e:
            logger.error(f"Failed to save mission simulation: {e}")
        return None

    def get_dashboard_stats(self, days: int = 14) -> dict[str, Any]:
        """
        Aggregate mission counts by status (all-time) and a daily mission
        count trend over the last `days` days (zero-filled for continuity),
        for the admin dashboard KPI cards and charts.
        """
        status_counts = {status.value: 0 for status in MissionStatus}
        for doc in self.db.missions.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}]):
            if doc["_id"] in status_counts:
                status_counts[doc["_id"]] = doc["count"]

        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        start_date = end_date - timedelta(days=days)

        daily_counts = {
            doc["_id"]: doc["count"]
            for doc in self.db.missions.aggregate(
                [
                    {"$match": {"scheduled_date": {"$gte": start_date, "$lt": end_date}}},
                    {
                        "$group": {
                            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$scheduled_date"}},
                            "count": {"$sum": 1},
                        }
                    },
                ]
            )
        }

        daily = []
        for i in range(days):
            day = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            daily.append({"date": day, "count": daily_counts.get(day, 0)})

        return {
            "total": sum(status_counts.values()),
            "by_status": status_counts,
            "daily": daily,
        }

    def get_missions_for_date(self, target_date: datetime) -> list[dict[str, Any]]:
        start_of_day = datetime(target_date.year, target_date.month, target_date.day)
        end_of_day = start_of_day + timedelta(days=1)

        # scheduled_date (the day the mission's deliveries are actually planned
        # for) — not created_at (an implementation detail of when the row was
        # inserted). Both usually coincide since generation runs once per day,
        # but scheduled_date is the field that means "today's missions".
        missions = list(self.db.missions.find({"scheduled_date": {"$gte": start_of_day, "$lt": end_of_day}}))
        
        # Load driver and vehicle information for each mission
        for mission in missions:
            if mission.get("driver_id"):
                driver = self.db.drivers.find_one({"_id": mission["driver_id"]})
                if driver:
                    mission["driver"] = driver
            if mission.get("vehicle_id"):
                vehicle = self.db.vehicles.find_one({"_id": mission["vehicle_id"]})
                if vehicle:
                    mission["vehicle"] = vehicle
        
        return [_serialize_mission(m) for m in missions]

    def get_missions_for_driver_today(self, driver_id: str) -> list[dict[str, Any]]:
        start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        missions = list(self.db.missions.find({
            "driver_id": ObjectId(driver_id),
            "scheduled_date": {"$gte": start_of_day, "$lt": end_of_day},
        }))
        return [_serialize_mission(m) for m in missions]

    def get_mission_by_id(self, mission_id: str) -> dict[str, Any] | None:
        mission = self.db.missions.find_one({"_id": mission_id})

        if mission:
            driver = self.db.drivers.find_one({"_id": mission["driver_id"]})
            vehicle = self.db.vehicles.find_one({"_id": mission["vehicle_id"]})
            if driver:
                mission["driver"] = driver
            if vehicle:
                mission["vehicle"] = vehicle

        return mission

    def update_mission_status(self, mission_id: str, status: MissionStatus) -> bool:
        try:
            result = self.db.missions.update_one(
                {"_id": mission_id},
                {"$set": {"status": status.value}},
            )
            if result.modified_count > 0:
                logger.info(f"Updated mission {mission_id} status to {status.value}")
                return True
        except Exception as e:
            logger.error(f"Failed to update mission status: {e}")
        return False

    def update_delivery_step_status(self, mission_id: str, step_index: int, is_done: bool) -> dict[str, Any] | None:
        try:
            mission = self.db.missions.find_one({"_id": ObjectId(mission_id)})
            if not mission:
                return None

            deliveries_order = mission.get("deliveries_order", [])
            if step_index < 0 or step_index >= len(deliveries_order):
                return None

            step = deliveries_order[step_index]
            step["is_done"] = is_done

            result = self.db.missions.update_one(
                {"_id": ObjectId(mission_id)},
                {"$set": {f"deliveries_order.{step_index}.is_done": is_done, "updated_at": datetime.utcnow()}},
            )

            if result.modified_count > 0:
                delivery_id = step.get("delivery_id")
                step_type = step.get("step_type")

                if delivery_id:
                    if step_type == "pickup" and is_done:
                        self.db.deliveries.update_one(
                            {"_id": ObjectId(delivery_id)},
                            {"$set": {"status": "picked", "updated_at": datetime.utcnow()}},
                        )
                    elif step_type == "delivery" and is_done:
                        self.db.deliveries.update_one(
                            {"_id": ObjectId(delivery_id)},
                            {"$set": {"status": "delivered", "delivered_at": datetime.utcnow(), "updated_at": datetime.utcnow()}},
                        )

                updated_mission = self.db.missions.find_one({"_id": ObjectId(mission_id)})
                if updated_mission:
                    return _serialize_mission(updated_mission)

        except Exception as e:
            logger.error(f"Failed to update delivery step status: {e}")

        return None

