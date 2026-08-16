import logging
from typing import Any

from app.algorithms.route_strategies import RouteOptimizationStrategy, SavingsRouteStrategy


logger = logging.getLogger(__name__)


class RouteOptimizerService:
    """Service for optimizing delivery routes within missions."""

    def __init__(self, db=None):
        """
        Initialize route optimizer service.

        Args:
            db: Optional database handle used to resolve the admin-configured active
                route strategy (mirrors CapacityOptimizer(db)). Without it, this
                service always uses SavingsRouteStrategy.
        """
        self.db = db

    def resolve_strategy(self) -> RouteOptimizationStrategy:
        """Resolve the strategy that would be used for the next optimize_mission_route()
        call without an explicit override — public so callers (e.g. the
        /test-generate route) can report which strategy will run before invoking it."""
        if self.db is not None:
            from app.services.optimization_settings_service import OptimizationSettingsService

            return OptimizationSettingsService(self.db).resolve_route_strategy()

        return SavingsRouteStrategy()

    def optimize_mission_route(
        self,
        deliveries: list[dict[str, Any]],
        start_location: tuple[float, float] | None = None,
        strategy: RouteOptimizationStrategy | None = None,
    ) -> dict[str, Any]:
        """
        Optimize the route for a mission's deliveries.

        Args:
            deliveries: List of delivery dictionaries with coordinates
            start_location: Optional starting (lat, lng) coordinate
            strategy: Optional strategy override, bypassing the admin-configured
                active one (used by POST /api/missions/test-generate to simulate a
                specific strategy without changing what's active in the database)

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

        resolved_strategy = strategy if strategy is not None else self.resolve_strategy()
        result = resolved_strategy.optimize(steps, start_location)

        logger.info(
            "Optimized route for %d deliveries using strategy '%s': %.2fkm, %ds",
            len(deliveries),
            resolved_strategy.strategy_name,
            result["total_distance"],
            result["estimated_duration"],
        )

        return result

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
