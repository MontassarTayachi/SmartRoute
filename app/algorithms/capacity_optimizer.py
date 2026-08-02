import logging
from typing import Any

logger = logging.getLogger(__name__)


class CapacityOptimizer:
    """Optimizer for vehicle capacity constraints in delivery assignment."""

    def assign_deliveries_to_vehicles(
        self,
        deliveries: list[dict[str, Any]],
        vehicles: list[dict[str, Any]],
        drivers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Assign deliveries to vehicles respecting capacity constraints.

        Args:
            deliveries: List of deliveries with 'weight_kg' and other metadata
            vehicles: List of vehicles with 'capacity_kg' and 'id'
            drivers: List of available drivers with 'id'

        Returns:
            List of assignments with driver_id, vehicle_id, and assigned deliveries
        """
        if not deliveries or not vehicles or not drivers:
            logger.warning("Missing data for capacity optimization")
            return []

        # Pair drivers with vehicles (assuming each driver has a vehicle)
        driver_vehicle_pairs = []
        for driver in drivers:
            vehicle_id = driver.get("assigned_vehicle_id")
            if vehicle_id:
                vehicle = next((v for v in vehicles if v.get("_id") == vehicle_id or v.get("id") == vehicle_id), None)
                if vehicle:
                    driver_vehicle_pairs.append(
                        {"driver_id": driver.get("_id", driver.get("id")), "vehicle_id": vehicle_id, "vehicle": vehicle}
                    )

        if not driver_vehicle_pairs:
            logger.warning("No driver-vehicle pairs found")
            return []

        # Sort deliveries by weight (heavier first for better packing)
        sorted_deliveries = sorted(deliveries, key=lambda d: d.get("weight_kg", 0), reverse=True)

        assignments = []
        for pair in driver_vehicle_pairs:
            assignments.append(
                {
                    "driver_id": pair["driver_id"],
                    "vehicle_id": pair["vehicle_id"],
                    "vehicle": pair["vehicle"],
                    "deliveries": [],
                    "total_weight": 0.0,
                }
            )

        # Assign deliveries using a greedy approach
        for delivery in sorted_deliveries:
            delivery_weight = delivery.get("weight_kg", 0)
            best_assignment = None
            best_remaining_capacity = float("inf")

            # Find the vehicle with the best remaining capacity
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
                    f"Could not assign delivery {delivery.get('_id', delivery.get('id'))} - no vehicle with sufficient capacity"
                )

        # Filter out assignments with no deliveries
        return [a for a in assignments if a["deliveries"]]

    def distribute_deliveries_by_region(
        self,
        region_deliveries: list[dict[str, Any]],
        drivers_in_region: list[dict[str, Any]],
        vehicles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Distribute deliveries within a region among available drivers.

        Args:
            region_deliveries: List of deliveries in the region
            drivers_in_region: List of drivers assigned to this region
            vehicles: List of all vehicles

        Returns:
            List of assignments for this region
        """
        if not region_deliveries:
            return []

        if not drivers_in_region:
            logger.warning(f"No drivers available for region with {len(region_deliveries)} deliveries")
            return []

        # Get vehicles for drivers in this region
        driver_vehicle_pairs = []
        for driver in drivers_in_region:
            vehicle_id = driver.get("assigned_vehicle_id")
            if vehicle_id:
                vehicle = next((v for v in vehicles if v.get("_id") == vehicle_id or v.get("id") == vehicle_id), None)
                if vehicle:
                    driver_vehicle_pairs.append(
                        {"driver_id": driver.get("_id", driver.get("id")), "vehicle_id": vehicle_id, "vehicle": vehicle}
                    )

        if not driver_vehicle_pairs:
            logger.warning("No vehicles available for drivers in region")
            return []

        # Calculate total capacity in the region
        total_capacity = sum(pair["vehicle"].get("capacity_kg", 0) for pair in driver_vehicle_pairs)
        total_weight = sum(d.get("weight_kg", 0) for d in region_deliveries)

        if total_weight > total_capacity:
            logger.warning(
                f"Total delivery weight ({total_weight}kg) exceeds total capacity ({total_capacity}kg)"
            )

        # Use the main assignment algorithm
        return self.assign_deliveries_to_vehicles(region_deliveries, vehicles, drivers_in_region)

    def validate_capacity(
        self, deliveries: list[dict[str, Any]], vehicle: dict[str, Any]
    ) -> bool:
        """
        Validate if a set of deliveries fits within vehicle capacity.

        Args:
            deliveries: List of deliveries with 'weight_kg'
            vehicle: Vehicle with 'capacity_kg'

        Returns:
            True if deliveries fit within capacity, False otherwise
        """
        total_weight = sum(d.get("weight_kg", 0) for d in deliveries)
        capacity = vehicle.get("capacity_kg", 0)
        return total_weight <= capacity
