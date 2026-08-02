import logging
from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId

from app.algorithms.capacity_optimizer import CapacityOptimizer
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
    return m


class MissionService:
    """Service for generating and managing delivery missions."""

    def __init__(self, db):
        self.db = db
        self.clustering_service = None
        self.driver_assignment_service = DriverAssignmentService()
        self.route_optimizer = RouteOptimizerService()
        self.capacity_optimizer = CapacityOptimizer()
        self.osm_routing_service = OSMRoutingService()

    def generate_missions_for_date(self, target_date: datetime | None = None) -> list[dict[str, Any]]:
        if target_date is None:
            target_date = datetime.utcnow()

        logger.info(f"Starting mission generation for date: {target_date.date()}")

        deliveries = self._get_deliveries_for_date(target_date)
        if not deliveries:
            logger.warning(f"No deliveries found for date {target_date.date()}")
            return []

        drivers = self._get_available_drivers()
        vehicles = self._get_available_vehicles()

        if not drivers:
            logger.warning("No available drivers found")
            return []
        if not vehicles:
            logger.warning("No available vehicles found")
            return []

        n_clusters = max(1, min(5, len(drivers)))
        self.clustering_service = ClusteringService(n_clusters=n_clusters)

        region_deliveries = self.clustering_service.cluster_deliveries(deliveries)
        region_centers = self.clustering_service.get_region_centers()
        region_drivers = self.driver_assignment_service.assign_drivers_to_regions(drivers, region_centers)

        all_missions = []
        for region_id, deliveries_in_region in region_deliveries.items():
            drivers_in_region = region_drivers.get(region_id, [])
            if not drivers_in_region:
                continue

            assignments = self.capacity_optimizer.distribute_deliveries_by_region(
                deliveries_in_region, drivers_in_region, vehicles
            )

            for assignment in assignments:
                mission = self._create_mission_from_assignment(assignment, region_id, target_date)
                if mission:
                    all_missions.append(mission)

        saved_missions = []
        for mission_dict in all_missions:
            saved = self._save_mission(mission_dict)
            if saved:
                saved_missions.append(saved)

        logger.info(f"Generated and saved {len(saved_missions)} missions")
        return saved_missions

    def _get_deliveries_for_date(self, target_date: datetime) -> list[dict[str, Any]]:
        start_of_day = datetime(target_date.year, target_date.month, target_date.day)
        end_of_day = start_of_day + timedelta(days=1)
        return list(self.db.deliveries.find({
            "scheduled_at": {"$gte": start_of_day, "$lt": end_of_day},
            "status": {"$in": ["pending", "assigned"]},
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
    ) -> dict[str, Any] | None:
        driver_id = assignment["driver_id"]
        vehicle_id = assignment["vehicle_id"]
        deliveries = assignment["deliveries"]

        if not deliveries:
            return None

        route_result = self.route_optimizer.optimize_mission_route(deliveries)

        driver = self.db.drivers.find_one({"_id": driver_id}) or self.db.drivers.find_one({"id": driver_id})
        start_location = None
        if driver:
            start_location = (
                driver.get("current_lat", deliveries[0].get("pickup_address_lat")),
                driver.get("current_lng", deliveries[0].get("pickup_address_lng")),
            )

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

    def _save_mission(self, mission_dict: dict[str, Any]) -> dict[str, Any] | None:
        try:
            mission_dict.pop("_id", None)
            result = self.db.missions.insert_one(mission_dict)
            if result.inserted_id:
                mission_dict["_id"] = str(result.inserted_id)
                logger.info(f"Saved mission {result.inserted_id}")
                return mission_dict
        except Exception as e:
            logger.error(f"Failed to save mission: {e}")
        return None

    def get_missions_for_date(self, target_date: datetime) -> list[dict[str, Any]]:
        start_of_day = datetime(target_date.year, target_date.month, target_date.day)
        end_of_day = start_of_day + timedelta(days=1)

        missions = list(self.db.missions.find({"created_at": {"$gte": start_of_day, "$lt": end_of_day}}))
        return [_serialize_mission(m) for m in missions]

    def get_missions_for_driver_today(self, driver_id: str) -> list[dict[str, Any]]:
        start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        missions = list(self.db.missions.find({
            "driver_id": ObjectId(driver_id),
            "created_at": {"$gte": start_of_day, "$lt": end_of_day},
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

