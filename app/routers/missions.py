from datetime import datetime, timedelta
import logging

from flask import Blueprint, current_app, jsonify, request

from app.core.exceptions import APIException
from app.dependencies import require_auth
from app.schemas.mission import (
    DeliveryStepUpdateRequest,
    MissionGenerateRequest,
    MissionUpdate,
)
from app.services.mission_service import MissionService

missions_bp = Blueprint("missions", __name__, url_prefix="/api/missions")
logger = logging.getLogger(__name__)


@missions_bp.route("/generate", methods=["POST"])
@require_auth
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
        result = mission_service.generate_missions_for_date(target_date)
        return jsonify(result), 200
    except Exception as e:
        raise APIException(500, f"Failed to generate missions: {str(e)}")


@missions_bp.route("/test-generate", methods=["POST"])
@require_auth
def test_generate_missions():
    from app.services.optimization_settings_service import build_route_strategy

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

    # Optional: force a specific route strategy for this simulation only, without
    # touching the admin-configured active one in route_strategy_settings. Lets an
    # admin compare strategies on the same real dataset before activating one.
    forced_route_strategy = None
    route_strategy_name = data.get("route_strategy")
    if route_strategy_name:
        forced_route_strategy = build_route_strategy(
            route_strategy_name, data.get("route_strategy_parameters") or {}
        )

    try:
        # Runs the exact same pipeline as /api/missions/generate
        # (MissionService._build_mission_drafts), but MissionService.
        # simulate_missions_for_date persists the result to
        # MISSION_SIMULATIONS_COLLECTION instead of `missions`, and never marks
        # deliveries as assigned — this request never adds or modifies anything in
        # `missions` or `deliveries`.
        result = mission_service.simulate_missions_for_date(target_date, route_strategy=forced_route_strategy)

        if result["stop_reason"] == "no_deliveries":
            return jsonify({
                "success": True,
                "total_deliveries": 0,
                "total_drivers_assigned": 0,
                "total_distance": 0.0,
                "total_assignments": 0,
                "assignments": [],
            }), 200

        if result["stop_reason"] in ("no_drivers", "no_vehicles"):
            return jsonify({
                "success": True,
                "total_deliveries": result["total_deliveries"],
                "total_drivers_assigned": 0,
                "total_distance": 0.0,
                "total_assignments": 0,
                "assignments": [],
                "message": "No available drivers or vehicles for simulation",
            }), 200

        assignments_summary = []
        total_distance = 0.0
        for mission in result["missions"]:
            route_distance = float(mission.get("route_distance", 0.0) or 0.0)
            total_distance += route_distance
            assignments_summary.append({
                "region_id": mission.get("region_id"),
                "driver_id": str(mission.get("driver_id")),
                "vehicle_id": str(mission.get("vehicle_id")),
                "delivery_count": len(mission.get("delivery_ids", [])),
                "total_weight": mission.get("total_weight", 0.0),
                "route_distance": route_distance,
                "estimated_duration": mission.get("route_duration", 0),
                "delivery_ids": [str(did) for did in mission.get("delivery_ids", [])],
                "deliveries_order": [
                    {
                        "delivery_id": str(step.get("delivery_id")),
                        "step_type": step.get("step_type"),
                        "order": step.get("order"),
                    }
                    for step in mission.get("deliveries_order", [])
                ],
            })

        total_deliveries_assigned = sum(a["delivery_count"] for a in assignments_summary)

        return jsonify({
            "success": True,
            "target_date": target_date.isoformat(),
            "total_deliveries": result["total_deliveries"],
            "total_drivers_assigned": len(assignments_summary),
            "total_distance": round(total_distance, 2),
            "total_assignments": len(assignments_summary),
            "assigned_deliveries": total_deliveries_assigned,
            "route_strategy_used": result["route_strategy_used"],
            "route_optimization_time_ms": round(result["route_optimization_time_ms"], 2),
            "simulation_run_id": result["simulation_run_id"],
            "assignments": assignments_summary,
        }), 200
    except Exception as e:
        raise APIException(500, f"Failed to simulate mission generation: {str(e)}")


@missions_bp.route("/today", methods=["GET"])
@require_auth
def get_today_missions():
    db = current_app.mongodb
    mission_service = MissionService(db)

    try:
        missions = mission_service.get_missions_for_date(datetime.utcnow())
        return jsonify({"items": missions}), 200
    except Exception as e:
        raise APIException(500, f"Failed to retrieve missions: {str(e)}")


@missions_bp.route("/stats", methods=["GET"])
@require_auth
def get_mission_stats():
    db = current_app.mongodb
    mission_service = MissionService(db)
    days = request.args.get("days", 14, type=int)

    try:
        return jsonify(mission_service.get_dashboard_stats(days=days)), 200
    except Exception as e:
        raise APIException(500, f"Failed to retrieve mission stats: {str(e)}")


@missions_bp.route("/driver/<driver_id>/today", methods=["GET"])
@require_auth
def get_driver_today_missions(driver_id):
    db = current_app.mongodb
    mission_service = MissionService(db)

    try:
        missions = mission_service.get_missions_for_driver_today(driver_id)
        return jsonify({"items": missions, "total": len(missions), "page": 1, "limit": len(missions)}), 200
    except Exception as e:
        raise APIException(500, f"Failed to retrieve driver missions: {str(e)}")


@missions_bp.route("/scheduler/status", methods=["GET"])
@require_auth
def get_scheduler_status():
    try:
        scheduler_service = getattr(current_app, "scheduler_service", None)
        if scheduler_service:
            return jsonify(scheduler_service.get_job_status()), 200
        return jsonify({"scheduler_running": False, "jobs": []}), 200
    except Exception as e:
        raise APIException(500, f"Failed to get scheduler status: {str(e)}")


@missions_bp.route("/assign", methods=["POST"])
@require_auth
def assign_deliveries():
    from app.services.clustering_service import ClusteringService
    from app.services.driver_assignment_service import DriverAssignmentService
    from app.algorithms.capacity_optimizer import CapacityOptimizer

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

        clustering_service = ClusteringService(db=db, driver_count=len(drivers))
        region_deliveries, deliveries_without_coordinates = clustering_service.cluster_deliveries(deliveries)
        region_centers = clustering_service.get_region_centers()

        # Intentionally uses optimize_driver_assignment (workload-first: busiest
        # regions get a driver before idle ones) rather than MissionService's
        # assign_drivers_to_regions (nearest-only), since this route serves
        # manual/on-demand assignment where driver scarcity should be resolved in
        # favor of the most loaded regions. See DriverAssignmentService.optimize_driver_assignment.
        driver_assignment_service = DriverAssignmentService()
        region_drivers = driver_assignment_service.optimize_driver_assignment(
            drivers, region_centers, region_deliveries
        )
        # See DriverAssignmentService.redistribute_orphaned_region_deliveries:
        # with more regions than drivers, some regions end up with no driver —
        # fold their deliveries into the nearest served region instead of
        # dropping them.
        region_deliveries = driver_assignment_service.redistribute_orphaned_region_deliveries(
            region_deliveries, region_drivers, region_centers
        )

        capacity_optimizer = CapacityOptimizer(db)
        # Reuses MissionService._create_mission_from_assignment/_save_mission —
        # the same route-ordering + real OSRM lookup + persistence used by
        # POST /api/missions/generate — instead of duplicating a Haversine-only,
        # polyline-less version here. Fixes a known, previously-documented
        # inconsistency where this route never called OSRM and always persisted
        # polyline=None.
        mission_service = MissionService(db)
        target_date = datetime.utcnow()

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

                mission_dict = mission_service._create_mission_from_assignment(
                    assignment, region_id, target_date
                )
                if not mission_dict:
                    continue

                # Matches generate_missions_for_date's convention: a delivery counts
                # as "assigned" as soon as a mission was built for it, regardless of
                # whether _save_mission below actually manages to persist it — see
                # MissionService._compute_unassigned_delivery_ids, reused at the end
                # of this route.
                assigned_delivery_ids.update(mission_dict["delivery_ids"])

                assignment_data = {
                    "driver_id": str(driver_id),
                    "driver_name": next((d.get("full_name") for d in drivers if str(d.get("_id")) == str(driver_id)), "Unknown"),
                    "vehicle_id": str(assignment["vehicle_id"]),
                    "vehicle_registration": next((v.get("registration") for v in vehicles if str(v.get("_id")) == str(assignment["vehicle_id"])), "Unknown"),
                    "region_id": region_id,
                    "delivery_ids": [str(did) for did in mission_dict["delivery_ids"]],
                    "total_weight": mission_dict["total_weight"],
                    "vehicle_capacity": assignment["vehicle"].get("capacity_kg", 0),
                    "route_distance": mission_dict["route_distance"],
                    "estimated_duration": mission_dict["route_duration"],
                    "deliveries_order": mission_dict["deliveries_order"],
                    "delivery_count": len(assignment["deliveries"]),
                    "polyline": mission_dict["polyline"],
                }

                saved = mission_service._save_mission(mission_dict)
                if saved:
                    assignment_data["mission_id"] = saved["_id"]
                else:
                    logger.error(f"Failed to create mission for driver {driver_id}")

                all_assignments.append(assignment_data)

        # Shared with MissionService.generate_missions_for_date: a delivery is
        # "unassigned" if it was part of the input set but never ended up in a saved
        # mission, whether because clustering excluded it (missing coordinates) or
        # no driver/vehicle capacity was available for its region.
        unassigned_delivery_ids = MissionService._compute_unassigned_delivery_ids(
            deliveries, assigned_delivery_ids
        )

        return jsonify({
            "success": True,
            "total_deliveries": len(deliveries),
            "total_assignments": len(all_assignments),
            "assigned_deliveries": len(assigned_delivery_ids),
            "unassigned_deliveries": len(unassigned_delivery_ids),
            "unassigned_delivery_ids": unassigned_delivery_ids,
            "n_clusters": clustering_service.n_clusters,
            "assignments": all_assignments,
        }), 200

    except APIException:
        raise
    except Exception as e:
        raise APIException(500, f"Failed to assign deliveries: {str(e)}")


# /<mission_id> routes must come after named routes like /today, /scheduler/status, /assign
@missions_bp.route("/<mission_id>", methods=["GET"])
@require_auth
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
@require_auth
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
@require_auth
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

