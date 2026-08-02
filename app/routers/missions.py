from datetime import datetime, timedelta
import logging

from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request

from app.core.exceptions import APIException
from app.schemas.mission import (
    DeliveryStepUpdateRequest,
    MissionGenerateRequest,
    MissionUpdate,
)
from app.services.mission_service import MissionService

missions_bp = Blueprint("missions", __name__, url_prefix="/api/missions")
logger = logging.getLogger(__name__)


@missions_bp.route("/generate", methods=["POST"])
def generate_missions():
    db = current_app.mongodb
    mission_service = MissionService(db)

    data = request.get_json(silent=True) or {}
    target_date = None
    if data.get("date"):
        try:
            target_date = datetime.fromisoformat(data["date"])
        except ValueError:
            return jsonify({"detail": "Date invalide."}), 400
    if target_date is None:
        target_date = datetime.utcnow()

    try:
        missions = mission_service.generate_missions_for_date(target_date)
        return jsonify(missions), 200
    except Exception as e:
        raise APIException(500, f"Failed to generate missions: {str(e)}")


@missions_bp.route("/today", methods=["GET"])
def get_today_missions():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    db = current_app.mongodb
    mission_service = MissionService(db)

    try:
        missions = mission_service.get_missions_for_date(datetime.utcnow())
        total = len(missions)
        start_idx = (page - 1) * limit
        paginated = missions[start_idx:start_idx + limit]
        return jsonify({"items": paginated, "total": total, "page": page, "limit": limit}), 200
    except Exception as e:
        raise APIException(500, f"Failed to retrieve missions: {str(e)}")


@missions_bp.route("/driver/<driver_id>/today", methods=["GET"])
def get_driver_today_missions(driver_id):
    db = current_app.mongodb
    mission_service = MissionService(db)

    try:
        missions = mission_service.get_missions_for_driver_today(driver_id)
        return jsonify({"items": missions, "total": len(missions), "page": 1, "limit": len(missions)}), 200
    except Exception as e:
        raise APIException(500, f"Failed to retrieve driver missions: {str(e)}")


@missions_bp.route("/scheduler/status", methods=["GET"])
def get_scheduler_status():
    try:
        scheduler_service = getattr(current_app, "scheduler_service", None)
        if scheduler_service:
            return jsonify(scheduler_service.get_job_status()), 200
        return jsonify({"scheduler_running": False, "jobs": []}), 200
    except Exception as e:
        raise APIException(500, f"Failed to get scheduler status: {str(e)}")


@missions_bp.route("/assign", methods=["POST"])
def assign_deliveries():
    from app.services.clustering_service import ClusteringService
    from app.services.driver_assignment_service import DriverAssignmentService
    from app.services.route_optimizer import RouteOptimizerService
    from app.algorithms.capacity_optimizer import CapacityOptimizer
    from app.models.mission import MissionStatus

    data = request.get_json(silent=True) or {}
    delivery_ids = data.get("delivery_ids")

    db = current_app.mongodb

    try:
        if delivery_ids:
            deliveries = list(db.deliveries.find({"_id": {"$in": delivery_ids}}))
        else:
            start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            deliveries = list(db.deliveries.find({
                "scheduled_at": {"$gte": start_of_day, "$lt": end_of_day},
                "status": {"$in": ["pending", "assigned"]},
            }))

        if not deliveries:
            raise APIException(404, "No deliveries found for assignment")

        drivers = list(db.drivers.find({"availability": "available"}))
        vehicles = list(db.vehicles.find({"status": "available"}))

        if not drivers:
            raise APIException(400, "No available drivers found")
        if not vehicles:
            raise APIException(400, "No available vehicles found")

        n_clusters = max(1, min(5, len(drivers)))
        clustering_service = ClusteringService(n_clusters=n_clusters)
        region_deliveries = clustering_service.cluster_deliveries(deliveries)
        region_centers = clustering_service.get_region_centers()

        driver_assignment_service = DriverAssignmentService()
        region_drivers = driver_assignment_service.optimize_driver_assignment(
            drivers, region_centers, region_deliveries
        )

        capacity_optimizer = CapacityOptimizer()
        route_optimizer = RouteOptimizerService()

        all_assignments = []
        assigned_delivery_ids = set()

        for region_id, deliveries_in_region in region_deliveries.items():
            drivers_in_region = region_drivers.get(region_id, [])
            if not drivers_in_region:
                continue

            assignments = capacity_optimizer.distribute_deliveries_by_region(
                deliveries_in_region, drivers_in_region, vehicles
            )

            for assignment in assignments:
                driver_id = assignment["driver_id"]
                route_result = route_optimizer.optimize_mission_route(assignment["deliveries"])

                steps_serializable = []
                for step in route_result["steps"]:
                    step_copy = step.copy()
                    step_copy["delivery_id"] = str(step.get("delivery_id"))
                    steps_serializable.append(step_copy)

                delivery_ids_local = [d.get("_id", d.get("id")) for d in assignment["deliveries"]]

                for delivery in assignment["deliveries"]:
                    did = delivery.get("_id", delivery.get("id"))
                    assigned_delivery_ids.add(did)
                    db.deliveries.update_one(
                        {"_id": did},
                        {"$set": {"driver_id": driver_id, "vehicle_id": assignment["vehicle_id"], "status": "assigned"}},
                    )

                assignment_data = {
                    "driver_id": str(driver_id),
                    "driver_name": next((d.get("full_name") for d in drivers if str(d.get("_id")) == str(driver_id)), "Unknown"),
                    "vehicle_id": str(assignment["vehicle_id"]),
                    "vehicle_registration": next((v.get("registration") for v in vehicles if str(v.get("_id")) == str(assignment["vehicle_id"])), "Unknown"),
                    "region_id": region_id,
                    "delivery_ids": [str(did) for did in delivery_ids_local],
                    "total_weight": assignment["total_weight"],
                    "vehicle_capacity": assignment["vehicle"].get("capacity_kg", 0),
                    "route_distance": route_result["total_distance"],
                    "estimated_duration": route_result["estimated_duration"],
                    "deliveries_order": steps_serializable,
                    "delivery_count": len(assignment["deliveries"]),
                }

                try:
                    mission_dict = {
                        "driver_id": driver_id,
                        "vehicle_id": assignment["vehicle_id"],
                        "region_id": region_id,
                        "delivery_ids": [ObjectId(did) if isinstance(did, str) else did for did in delivery_ids_local],
                        "deliveries_order": steps_serializable,
                        "total_weight": assignment["total_weight"],
                        "route_distance": route_result["total_distance"],
                        "route_duration": route_result["estimated_duration"],
                        "status": MissionStatus.planned.value,
                        "polyline": None,
                        "scheduled_date": datetime.utcnow(),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                    result = db.missions.insert_one(mission_dict)
                    if result.inserted_id:
                        assignment_data["mission_id"] = str(result.inserted_id)
                except Exception as e:
                    logger.error(f"Failed to create mission for driver {driver_id}: {e}")

                all_assignments.append(assignment_data)

        all_delivery_ids = {d.get("_id", d.get("id")) for d in deliveries}
        unassigned = all_delivery_ids - assigned_delivery_ids

        return jsonify({
            "success": True,
            "total_deliveries": len(deliveries),
            "total_assignments": len(all_assignments),
            "assigned_deliveries": len(assigned_delivery_ids),
            "unassigned_deliveries": len(unassigned),
            "unassigned_delivery_ids": [str(did) for did in unassigned],
            "n_clusters": n_clusters,
            "assignments": all_assignments,
        }), 200

    except APIException:
        raise
    except Exception as e:
        raise APIException(500, f"Failed to assign deliveries: {str(e)}")


# /<mission_id> routes must come after named routes like /today, /scheduler/status, /assign
@missions_bp.route("/<mission_id>", methods=["GET"])
def get_mission(mission_id):
    db = current_app.mongodb
    mission_service = MissionService(db)

    try:
        mission = mission_service.get_mission_by_id(mission_id)
        if not mission:
            raise APIException(404, f"Mission {mission_id} not found")
        return jsonify(mission), 200
    except APIException:
        raise
    except Exception as e:
        raise APIException(500, f"Failed to retrieve mission: {str(e)}")


@missions_bp.route("/<mission_id>", methods=["PATCH"])
def update_mission(mission_id):
    db = current_app.mongodb
    mission_service = MissionService(db)

    data = request.get_json(silent=True) or {}
    try:
        mission_update = MissionUpdate(**data)
    except Exception:
        return jsonify({"detail": "Données invalides."}), 422

    try:
        existing_mission = mission_service.get_mission_by_id(mission_id)
        if not existing_mission:
            raise APIException(404, f"Mission {mission_id} not found")

        if mission_update.status:
            from app.models.mission import MissionStatus as MissionStatusEnum
            status_enum = MissionStatusEnum(mission_update.status.value)
            success = mission_service.update_mission_status(mission_id, status_enum)
            if not success:
                raise APIException(500, "Failed to update mission status")

        if mission_update.polyline is not None:
            db.missions.update_one(
                {"_id": mission_id},
                {"$set": {"polyline": mission_update.polyline}},
            )

        updated = mission_service.get_mission_by_id(mission_id)
        return jsonify(updated), 200

    except APIException:
        raise
    except Exception as e:
        raise APIException(500, f"Failed to update mission: {str(e)}")


@missions_bp.route("/<mission_id>/step", methods=["PATCH"])
def update_delivery_step(mission_id):
    db = current_app.mongodb
    mission_service = MissionService(db)

    data = request.get_json(silent=True) or {}
    try:
        step_update = DeliveryStepUpdateRequest(**data)
    except Exception:
        return jsonify({"detail": "Données invalides."}), 422

    try:
        updated_mission = mission_service.update_delivery_step_status(
            mission_id, step_update.step_index, step_update.is_done
        )
        if not updated_mission:
            raise APIException(404, f"Mission {mission_id} not found or invalid step index")
        return jsonify(updated_mission), 200

    except APIException:
        raise
    except Exception as e:
        raise APIException(500, f"Failed to update delivery step: {str(e)}")

