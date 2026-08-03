import logging
from typing import Any

from app.algorithms.nearest_neighbor import NearestNeighborOptimizer
from app.algorithms.route_refiner import RouteRefiner


logger = logging.getLogger(__name__)


class RouteOptimizerService:
    """Service for optimizing delivery routes within missions."""

    def __init__(self):
        """Initialize route optimizer service."""
        self.nn_optimizer = NearestNeighborOptimizer()
        self.route_refiner = RouteRefiner(max_iterations=100)

    @staticmethod
    def _build_distance_matrix(
        steps: list[dict[str, Any]],
        start_location: tuple[float, float] | None = None,
    ) -> list[list[float]]:
        matrix_steps = []
        if start_location is not None:
            matrix_steps.append({"lat": start_location[0], "lng": start_location[1]})
        matrix_steps.extend(steps)

        matrix: list[list[float]] = []
        for source in matrix_steps:
            row = []
            for target in matrix_steps:
                row.append(
                    NearestNeighborOptimizer.haversine_distance(
                        source["lat"],
                        source["lng"],
                        target["lat"],
                        target["lng"],
                    )
                )
            matrix.append(row)

        return matrix

    @staticmethod
    def _annotate_steps_for_refinement(
        steps: list[dict[str, Any]],
        start_location: tuple[float, float] | None = None,
    ) -> list[dict[str, Any]]:
        offset = 1 if start_location is not None else 0
        annotated_steps = []
        for index, step in enumerate(steps):
            step_copy = step.copy()
            step_copy["_matrix_index"] = index + offset
            annotated_steps.append(step_copy)
        return annotated_steps

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

            if pickup_lat is not None and pickup_lng is not None:
                steps.append(
                    {
                        "delivery_id": delivery_id,
                        "step_type": "pickup",
                        "address": pickup_address,
                        "lat": pickup_lat,
                        "lng": pickup_lng,
                    }
                )

            if dropoff_lat is not None and dropoff_lng is not None:
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
        before_refinement_distance = self.nn_optimizer.calculate_total_distance(
            optimized_steps, start_location
        )

        distance_matrix = self._build_distance_matrix(optimized_steps, start_location)
        refinement_input = self._annotate_steps_for_refinement(optimized_steps, start_location)
        refined_steps = self.route_refiner.two_opt(refinement_input, distance_matrix)
        refined_steps = self.route_refiner.or_opt(refined_steps, distance_matrix)
        for step in refined_steps:
            step.pop("_matrix_index", None)
        after_refinement_distance = self.nn_optimizer.calculate_total_distance(
            refined_steps, start_location
        )

        if after_refinement_distance + 1e-9 < before_refinement_distance:
            logger.info(
                "Route refinement improved distance from %.2fkm to %.2fkm (gain %.2fkm)",
                before_refinement_distance,
                after_refinement_distance,
                before_refinement_distance - after_refinement_distance,
            )
        else:
            logger.info(
                "Route refinement completed with no distance gain (%.2fkm)",
                after_refinement_distance,
            )

        # Calculate total distance
        total_distance = after_refinement_distance

        # Estimate duration (assuming average speed of 30 km/h in urban areas)
        avg_speed_kmh = 30.0
        estimated_duration_seconds = int((total_distance / avg_speed_kmh) * 3600)

        # Add order to steps
        for order, step in enumerate(refined_steps):
            step["order"] = order

        logger.info(
            f"Optimized route for {len(deliveries)} deliveries: "
            f"{total_distance:.2f}km, {estimated_duration_seconds}s"
        )

        return {
            "steps": refined_steps,
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
