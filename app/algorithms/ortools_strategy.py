from __future__ import annotations

import logging
from typing import Any

from app.algorithms.nearest_neighbor import NearestNeighborOptimizer
from app.algorithms.route_strategies import (
    RouteOptimizationStrategy,
    SavingsRouteStrategy,
    estimate_duration_seconds,
    respects_pickup_before_delivery,
)


logger = logging.getLogger(__name__)

DEFAULT_TIME_LIMIT_SECONDS = 5
# Distances are converted from km to this many integer units (meters) since
# OR-Tools' routing solver requires integer arc costs.
DISTANCE_SCALE = 1000


class ORToolsRouteStrategy(RouteOptimizationStrategy):
    """
    Solves the mission route as a single-vehicle pickup-and-delivery problem using
    Google OR-Tools (ortools.constraint_solver.pywrapcp), with a pickup-before-delivery
    precedence constraint per delivery_id.

    OR-Tools is only imported when this strategy actually runs, so the rest of the
    app (including SavingsRouteStrategy, the default/fallback) works even in an
    environment where the ortools package is not installed.

    time_limit_seconds (via self.parameters, default 5) bounds the solver's search
    so a large mission can't stall mission generation indefinitely. If the solver
    finds no admissible solution within that time (or raises), this strategy logs a
    warning and falls back to SavingsRouteStrategy rather than failing the caller.
    """

    strategy_name = "ortools_cvrp"

    def __init__(self, parameters: dict[str, Any] | None = None):
        super().__init__(parameters)
        self._fallback = SavingsRouteStrategy()

    def optimize(
        self,
        steps: list[dict[str, Any]],
        start_location: tuple[float, float] | None = None,
    ) -> dict[str, Any]:
        if not steps:
            return {"steps": [], "total_distance": 0.0, "estimated_duration": 0}

        if len(steps) == 1:
            return self._fallback.optimize(steps, start_location)

        try:
            ordered_steps = self._solve(steps, start_location)
        except Exception:
            logger.warning(
                "OR-Tools route solver raised an exception; falling back to SavingsRouteStrategy.",
                exc_info=True,
            )
            return self._fallback.optimize(steps, start_location)

        if ordered_steps is None:
            logger.warning(
                "OR-Tools route solver found no admissible solution within the time "
                "limit; falling back to SavingsRouteStrategy."
            )
            return self._fallback.optimize(steps, start_location)

        total_distance = NearestNeighborOptimizer().calculate_total_distance(ordered_steps, start_location)
        for order, step in enumerate(ordered_steps):
            step["order"] = order

        return {
            "steps": ordered_steps,
            "total_distance": total_distance,
            "estimated_duration": estimate_duration_seconds(total_distance),
        }

    def _solve(
        self,
        steps: list[dict[str, Any]],
        start_location: tuple[float, float] | None,
    ) -> list[dict[str, Any]] | None:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2

        depot_lat, depot_lng = start_location if start_location else (steps[0]["lat"], steps[0]["lng"])
        # Node 0 is always a depot (real start_location, or a proxy located at the
        # first step when none was given, mirroring NearestNeighborOptimizer's
        # convention). Nodes 1..n map 1:1 to `steps`.
        nodes = [{"lat": depot_lat, "lng": depot_lng}] + steps
        n_total = len(nodes)

        distance_matrix = self._build_scaled_matrix(nodes)

        manager = pywrapcp.RoutingIndexManager(n_total, 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Cumulative distance dimension: used purely to compare relative position of
        # pickup vs. delivery nodes along the route (pickup's cumulative distance
        # must be <= delivery's), not as a real capacity/time constraint.
        routing.AddDimension(
            transit_callback_index,
            0,
            DISTANCE_SCALE * 1_000_000,
            True,
            "Distance",
        )
        distance_dimension = routing.GetDimensionOrDie("Distance")

        node_index_by_step_id = {id(step): position + 1 for position, step in enumerate(steps)}
        pickup_node_by_delivery: dict[Any, int] = {}
        delivery_node_by_delivery: dict[Any, int] = {}
        for step in steps:
            delivery_id = step["delivery_id"]
            node_index = node_index_by_step_id[id(step)]
            if step["step_type"] == "pickup":
                pickup_node_by_delivery[delivery_id] = node_index
            else:
                delivery_node_by_delivery[delivery_id] = node_index

        for delivery_id, pickup_node in pickup_node_by_delivery.items():
            delivery_node = delivery_node_by_delivery.get(delivery_id)
            if delivery_node is None:
                continue
            pickup_index = manager.NodeToIndex(pickup_node)
            delivery_index = manager.NodeToIndex(delivery_node)
            routing.AddPickupAndDelivery(pickup_index, delivery_index)
            routing.solver().Add(routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))
            routing.solver().Add(
                distance_dimension.CumulVar(pickup_index) <= distance_dimension.CumulVar(delivery_index)
            )

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        time_limit_seconds = self.parameters.get("time_limit_seconds", DEFAULT_TIME_LIMIT_SECONDS)
        search_parameters.time_limit.FromSeconds(int(time_limit_seconds))

        solution = routing.SolveWithParameters(search_parameters)
        if solution is None:
            return None

        ordered_steps = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                ordered_steps.append(steps[node - 1].copy())
            index = solution.Value(routing.NextVar(index))

        if len(ordered_steps) != len(steps) or not respects_pickup_before_delivery(ordered_steps):
            return None

        return ordered_steps

    @staticmethod
    def _build_scaled_matrix(nodes: list[dict[str, Any]]) -> list[list[int]]:
        n = len(nodes)
        matrix = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                matrix[i][j] = round(
                    NearestNeighborOptimizer.haversine_distance(
                        nodes[i]["lat"], nodes[i]["lng"], nodes[j]["lat"], nodes[j]["lng"]
                    )
                    * DISTANCE_SCALE
                )
        # Returning to the depot is free: this is a single open-path route (the
        # driver doesn't need to drive back to the start), not a closed tour, so the
        # solver shouldn't optimize for (or be constrained by) a return leg.
        for i in range(n):
            matrix[i][0] = 0
        return matrix
