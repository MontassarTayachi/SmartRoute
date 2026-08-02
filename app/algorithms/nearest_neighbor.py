import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


class NearestNeighborOptimizer:
    """Nearest Neighbor algorithm for route optimization."""

    @staticmethod
    def haversine_distance(
        lat1: float, lng1: float, lat2: float, lng2: float
    ) -> float:
        """
        Calculate the Haversine distance between two coordinates in kilometers.

        Args:
            lat1, lng1: Latitude and longitude of first point
            lat2, lng2: Latitude and longitude of second point

        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def optimize_route(
        self,
        steps: list[dict[str, Any]],
        start_location: tuple[float, float] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Optimize the order of delivery steps using Nearest Neighbor algorithm.

        Args:
            steps: List of delivery steps with 'lat', 'lng', and 'delivery_id'
            start_location: Optional starting (lat, lng) coordinate

        Returns:
            Optimized list of steps in order
        """
        if not steps:
            return []

        if len(steps) == 1:
            return steps

        # Create a copy to avoid modifying the original
        unvisited = steps.copy()
        optimized_route = []

        # Start from the specified location or the first step
        current_lat, current_lng = (
            start_location if start_location else (unvisited[0]["lat"], unvisited[0]["lng"])
        )

        # Build pickup-delivery pairs mapping
        pickup_delivery_map = {}
        for step in steps:
            delivery_id = step["delivery_id"]
            if delivery_id not in pickup_delivery_map:
                pickup_delivery_map[delivery_id] = {"pickup": None, "delivery": None}
            if step["step_type"] == "pickup":
                pickup_delivery_map[delivery_id]["pickup"] = step
            else:
                pickup_delivery_map[delivery_id]["delivery"] = step

        while unvisited:
            # Find the nearest unvisited step
            nearest_step = None
            nearest_distance = float("inf")

            for step in unvisited:
                # Check constraint: pickup must be visited before delivery
                if step["step_type"] == "delivery":
                    delivery_id = step["delivery_id"]
                    pickup_step = pickup_delivery_map[delivery_id]["pickup"]
                    # If pickup not yet visited, skip this delivery
                    if pickup_step and pickup_step in unvisited:
                        continue

                distance = self.haversine_distance(
                    current_lat, current_lng, step["lat"], step["lng"]
                )

                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_step = step

            if nearest_step:
                optimized_route.append(nearest_step)
                unvisited.remove(nearest_step)
                current_lat, current_lng = nearest_step["lat"], nearest_step["lng"]
            else:
                # No valid step found (shouldn't happen with proper data)
                logger.warning("No valid step found in nearest neighbor optimization")
                break

        return optimized_route

    def calculate_total_distance(
        self, steps: list[dict[str, Any]], start_location: tuple[float, float] | None = None
    ) -> float:
        """
        Calculate the total distance of a route.

        Args:
            steps: List of steps in order
            start_location: Optional starting (lat, lng) coordinate

        Returns:
            Total distance in kilometers
        """
        if not steps:
            return 0.0

        total_distance = 0.0

        if start_location:
            current_lat, current_lng = start_location
        else:
            current_lat, current_lng = steps[0]["lat"], steps[0]["lng"]

        for step in steps:
            distance = self.haversine_distance(
                current_lat, current_lng, step["lat"], step["lng"]
            )
            total_distance += distance
            current_lat, current_lng = step["lat"], step["lng"]

        return total_distance
