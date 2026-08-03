from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any


logger = logging.getLogger(__name__)


class AssignmentAlgorithm(ABC):
    """Common interface for delivery-to-vehicle assignment strategies."""

    algorithm_name = "base"

    def __init__(self, parameters: dict[str, Any] | None = None):
        self.parameters = parameters or {}

    @abstractmethod
    def assign(
        self,
        deliveries: list[dict[str, Any]],
        vehicles: list[dict[str, Any]],
        drivers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @staticmethod
    def _build_driver_vehicle_pairs(
        vehicles: list[dict[str, Any]],
        drivers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        driver_vehicle_pairs = []
        for driver in drivers:
            vehicle_id = driver.get("assigned_vehicle_id")
            if not vehicle_id:
                continue

            vehicle = next(
                (v for v in vehicles if v.get("_id") == vehicle_id or v.get("id") == vehicle_id),
                None,
            )
            if vehicle:
                driver_vehicle_pairs.append(
                    {
                        "driver_id": driver.get("_id", driver.get("id")),
                        "vehicle_id": vehicle_id,
                        "vehicle": vehicle,
                    }
                )

        return driver_vehicle_pairs

    @staticmethod
    def _initialize_assignments(driver_vehicle_pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "driver_id": pair["driver_id"],
                "vehicle_id": pair["vehicle_id"],
                "vehicle": pair["vehicle"],
                "deliveries": [],
                "total_weight": 0.0,
            }
            for pair in driver_vehicle_pairs
        ]


class GreedyCapacityAlgorithm(AssignmentAlgorithm):
    """Current greedy strategy that fills the most fitting vehicle first."""

    algorithm_name = "greedy_capacity"

    def assign(
        self,
        deliveries: list[dict[str, Any]],
        vehicles: list[dict[str, Any]],
        drivers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not deliveries or not vehicles or not drivers:
            logger.warning("Missing data for capacity optimization")
            return []

        driver_vehicle_pairs = self._build_driver_vehicle_pairs(vehicles, drivers)
        if not driver_vehicle_pairs:
            logger.warning("No driver-vehicle pairs found")
            return []

        sorted_deliveries = sorted(deliveries, key=lambda d: d.get("weight_kg", 0), reverse=True)
        assignments = self._initialize_assignments(driver_vehicle_pairs)

        for delivery in sorted_deliveries:
            delivery_weight = delivery.get("weight_kg", 0)
            best_assignment = None
            best_remaining_capacity = float("inf")

            for assignment in assignments:
                vehicle_capacity = assignment["vehicle"].get("capacity_kg", 0)
                current_weight = assignment["total_weight"]
                remaining_capacity = vehicle_capacity - current_weight - delivery_weight

                if remaining_capacity >= 0 and remaining_capacity < best_remaining_capacity:
                    best_remaining_capacity = remaining_capacity
                    best_assignment = assignment

            if best_assignment:
                best_assignment["deliveries"].append(delivery)
                best_assignment["total_weight"] += delivery_weight
            else:
                logger.warning(
                    "Could not assign delivery %s - no vehicle with sufficient capacity",
                    delivery.get("_id", delivery.get("id")),
                )

        return [assignment for assignment in assignments if assignment["deliveries"]]


class BalancedLoadAlgorithm(AssignmentAlgorithm):
    """Alternative strategy that prefers the most balanced normalized load."""

    algorithm_name = "balanced_load"

    def assign(
        self,
        deliveries: list[dict[str, Any]],
        vehicles: list[dict[str, Any]],
        drivers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not deliveries or not vehicles or not drivers:
            logger.warning("Missing data for capacity optimization")
            return []

        driver_vehicle_pairs = self._build_driver_vehicle_pairs(vehicles, drivers)
        if not driver_vehicle_pairs:
            logger.warning("No driver-vehicle pairs found")
            return []

        sorted_deliveries = sorted(deliveries, key=lambda d: d.get("weight_kg", 0), reverse=True)
        assignments = self._initialize_assignments(driver_vehicle_pairs)

        for delivery in sorted_deliveries:
            delivery_weight = delivery.get("weight_kg", 0)
            best_assignment = None
            best_score = float("inf")
            best_remaining_capacity = float("inf")

            for assignment_index, assignment in enumerate(assignments):
                capacity = assignment["vehicle"].get("capacity_kg", 0)
                current_weight = assignment["total_weight"]
                remaining_capacity = capacity - current_weight - delivery_weight

                if remaining_capacity < 0 or capacity <= 0:
                    continue

                projected_loads = [assignment_state["total_weight"] for assignment_state in assignments]
                projected_loads[assignment_index] = current_weight + delivery_weight
                mean_load = sum(projected_loads) / len(projected_loads)
                projected_variance = sum((load - mean_load) ** 2 for load in projected_loads) / len(projected_loads)

                if (
                    projected_variance < best_score
                    or (
                        abs(projected_variance - best_score) < 1e-9
                        and remaining_capacity < best_remaining_capacity
                    )
                ):
                    best_score = projected_variance
                    best_remaining_capacity = remaining_capacity
                    best_assignment = assignment

            if best_assignment:
                best_assignment["deliveries"].append(delivery)
                best_assignment["total_weight"] += delivery_weight
            else:
                logger.warning(
                    "Could not assign delivery %s - no vehicle with sufficient capacity",
                    delivery.get("_id", delivery.get("id")),
                )

        return [assignment for assignment in assignments if assignment["deliveries"]]