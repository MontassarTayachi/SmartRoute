import logging
from typing import Any

from app.algorithms.nearest_neighbor import NearestNeighborOptimizer


logger = logging.getLogger(__name__)


class RouteOptimizerService:
    """Service for optimizing delivery routes within missions."""

    def __init__(self):
        """Initialize route optimizer service."""
        self.nn_optimizer = NearestNeighborOptimizer()

    def optimize_mission_route(
        self,
        deliveries: list[dict[str, Any]],
        start_location: tuple[float, float] | None = None,
    ) -> dict[str, Any]:
        """
        Optimize the route for a mission's deliveries.

        Args:
            deliveries: List of delivery dictionaries with coordinates
            start_location: Optional starting (lat, lng) coordinate

        Returns:
            Dictionary with optimized steps, total distance, and estimated duration
        """
        if not deliveries:
            logger.warning("No deliveries provided for route optimization")
            return {
                "steps": [],
                "total_distance": 0.0,
                "estimated_duration": 0,
            }

        # Build delivery steps (pickup and delivery for each delivery)
        steps = []
        for delivery in deliveries:
            delivery_id = delivery.get("_id", delivery.get("id"))
            pickup_lat = delivery.get("pickup_address_lat")
            pickup_lng = delivery.get("pickup_address_lng")
            pickup_address = delivery.get("pickup_address")
            dropoff_lat = delivery.get("dropoff_address_lat")
            dropoff_lng = delivery.get("dropoff_address_lng")
            dropoff_address = delivery.get("dropoff_address")

            if pickup_lat and pickup_lng:
                steps.append(
                    {
                        "delivery_id": delivery_id,
                        "step_type": "pickup",
                        "address": pickup_address,
                        "lat": pickup_lat,
                        "lng": pickup_lng,
                    }
                )

            if dropoff_lat and dropoff_lng:
                steps.append(
                    {
                        "delivery_id": delivery_id,
                        "step_type": "delivery",
                        "address": dropoff_address,
                        "lat": dropoff_lat,
                        "lng": dropoff_lng,
                    }
                )

        # Optimize route using nearest neighbor
        optimized_steps = self.nn_optimizer.optimize_route(steps, start_location)

        # Calculate total distance
        total_distance = self.nn_optimizer.calculate_total_distance(
            optimized_steps, start_location
        )

        # Estimate duration (assuming average speed of 30 km/h in urban areas)
        avg_speed_kmh = 30.0
        estimated_duration_seconds = int((total_distance / avg_speed_kmh) * 3600)

        # Add order to steps
        for order, step in enumerate(optimized_steps):
            step["order"] = order

        logger.info(
            f"Optimized route for {len(deliveries)} deliveries: "
            f"{total_distance:.2f}km, {estimated_duration_seconds}s"
        )

        return {
            "steps": optimized_steps,
            "total_distance": total_distance,
            "estimated_duration": estimated_duration_seconds,
        }

    def validate_route_constraints(
        self, steps: list[dict[str, Any]]
    ) -> bool:
        """
        Validate that the route respects pickup-before-delivery constraints.

        Args:
            steps: List of ordered steps

        Returns:
            True if constraints are satisfied, False otherwise
        """
        delivery_pickup_orders = {}

        for step in steps:
            delivery_id = step["delivery_id"]
            step_type = step["step_type"]
            order = step["order"]

            if step_type == "pickup":
                delivery_pickup_orders[delivery_id] = order
            elif step_type == "delivery":
                pickup_order = delivery_pickup_orders.get(delivery_id)
                if pickup_order is None:
                    logger.warning(
                        f"Delivery {delivery_id} has delivery step without pickup"
                    )
                    return False
                if pickup_order > order:
                    logger.warning(
                        f"Delivery {delivery_id} has pickup after delivery "
                        f"(pickup: {pickup_order}, delivery: {order})"
                    )
                    return False

        return True
