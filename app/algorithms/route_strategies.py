from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.algorithms.nearest_neighbor import NearestNeighborOptimizer
from app.algorithms.route_refiner import RouteRefiner


logger = logging.getLogger(__name__)

AVG_SPEED_KMH = 30.0


def estimate_duration_seconds(total_distance_km: float) -> int:
    """Estimate travel duration assuming an average urban speed of 30 km/h."""
    return int((total_distance_km / AVG_SPEED_KMH) * 3600)


def respects_pickup_before_delivery(steps: list[dict[str, Any]]) -> bool:
    """Check that every delivery's pickup step comes before its delivery step."""
    pickup_positions: dict[Any, int] = {}
    for position, step in enumerate(steps):
        delivery_id = step.get("delivery_id")
        step_type = step.get("step_type")
        if delivery_id is None or step_type not in {"pickup", "delivery"}:
            return False
        if step_type == "pickup":
            pickup_positions[delivery_id] = position
            continue
        pickup_position = pickup_positions.get(delivery_id)
        if pickup_position is None or pickup_position > position:
            return False
    return True


def build_distance_matrix(
    steps: list[dict[str, Any]],
    start_location: tuple[float, float] | None = None,
) -> list[list[float]]:
    """Build a Haversine distance matrix, prepending a start node when provided."""
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
                    source["lat"], source["lng"], target["lat"], target["lng"]
                )
            )
        matrix.append(row)
    return matrix


def annotate_steps_for_refinement(
    steps: list[dict[str, Any]],
    start_location: tuple[float, float] | None = None,
) -> list[dict[str, Any]]:
    """Attach the matrix index each step maps to in build_distance_matrix's output."""
    offset = 1 if start_location is not None else 0
    annotated_steps = []
    for index, step in enumerate(steps):
        step_copy = step.copy()
        step_copy["_matrix_index"] = index + offset
        annotated_steps.append(step_copy)
    return annotated_steps


class RouteOptimizationStrategy(ABC):
    """Interface commune pour les stratégies d'ordonnancement de tournée."""

    strategy_name = "base"

    def __init__(self, parameters: dict[str, Any] | None = None):
        self.parameters = parameters or {}

    @abstractmethod
    def optimize(
        self,
        steps: list[dict[str, Any]],
        start_location: tuple[float, float] | None = None,
    ) -> dict[str, Any]:
        """
        Doit retourner:
        {
            "steps": [...],           # étapes ordonnées avec "order"
            "total_distance": float,  # km
            "estimated_duration": int # secondes
        }
        Doit respecter la contrainte pickup avant delivery pour chaque delivery_id.
        """
        raise NotImplementedError


class SavingsRouteStrategy(RouteOptimizationStrategy):
    """
    Clarke & Wright savings construction, refined with the existing RouteRefiner
    (2-opt then Or-opt). This is the fast, dependency-free default strategy that
    OptimizationSettingsService.resolve_route_strategy() falls back to.

    NearestNeighborOptimizer is kept and encapsulated here (not deleted): its
    construction is run alongside Clarke & Wright's, both independently refined by
    RouteRefiner, and the cheaper of the two results is returned. Clarke & Wright
    savings merges are a good heuristic but are not guaranteed to always beat
    nearest-neighbor construction on every instance (different local optima after
    refinement) — comparing both is what makes this strategy's output distance
    always <= the previous nearest-neighbor + 2-opt/Or-opt baseline, as required.
    """

    strategy_name = "clarke_wright"

    def __init__(self, parameters: dict[str, Any] | None = None):
        super().__init__(parameters)
        self._nn_fallback = NearestNeighborOptimizer()
        self._refiner = RouteRefiner(max_iterations=100)

    def optimize(
        self,
        steps: list[dict[str, Any]],
        start_location: tuple[float, float] | None = None,
    ) -> dict[str, Any]:
        if not steps:
            return {"steps": [], "total_distance": 0.0, "estimated_duration": 0}

        if len(steps) == 1:
            single_step = steps[0].copy()
            single_step["order"] = 0
            total_distance = 0.0
            if start_location is not None:
                total_distance = NearestNeighborOptimizer.haversine_distance(
                    start_location[0], start_location[1], single_step["lat"], single_step["lng"]
                )
            return {
                "steps": [single_step],
                "total_distance": total_distance,
                "estimated_duration": estimate_duration_seconds(total_distance),
            }

        candidates = []

        cw_route = self._clarke_wright_construct(steps, start_location)
        if cw_route is not None and respects_pickup_before_delivery(cw_route):
            candidates.append(self._refine(cw_route, start_location))
        else:
            logger.warning(
                "Clarke & Wright construction could not satisfy pickup-before-delivery "
                "constraints; using nearest-neighbor construction only."
            )

        nn_route = self._nn_fallback.optimize_route(steps, start_location)
        candidates.append(self._refine(nn_route, start_location))

        return min(candidates, key=lambda candidate: candidate["total_distance"])

    def _refine(
        self,
        route: list[dict[str, Any]],
        start_location: tuple[float, float] | None,
    ) -> dict[str, Any]:
        distance_matrix = build_distance_matrix(route, start_location)
        refinement_input = annotate_steps_for_refinement(route, start_location)
        refined_steps = self._refiner.two_opt(refinement_input, distance_matrix)
        refined_steps = self._refiner.or_opt(refined_steps, distance_matrix)
        for step in refined_steps:
            step.pop("_matrix_index", None)

        total_distance = self._nn_fallback.calculate_total_distance(refined_steps, start_location)

        for order, step in enumerate(refined_steps):
            step["order"] = order

        return {
            "steps": refined_steps,
            "total_distance": total_distance,
            "estimated_duration": estimate_duration_seconds(total_distance),
        }

    @staticmethod
    def _clarke_wright_construct(
        steps: list[dict[str, Any]],
        start_location: tuple[float, float] | None,
    ) -> list[dict[str, Any]] | None:
        """
        Classic Clarke & Wright savings merge, adapted to build a single tour (no
        vehicle-capacity cap since these steps already belong to one mission/driver):
        start with one singleton route per step, then repeatedly merge the pair of
        routes with the highest savings s(i,j) = d(depot,i) + d(depot,j) - d(i,j),
        only when i/j are route endpoints and the merge keeps every pickup before
        its matching delivery. Once no more positive-savings merges are feasible,
        remaining route fragments are force-merged (nearest endpoints first) into
        the single final tour a mission route requires.
        """
        n = len(steps)
        depot_lat, depot_lng = start_location if start_location else (steps[0]["lat"], steps[0]["lng"])

        def dist(a_idx: int, b_idx: int) -> float:
            a, b = steps[a_idx], steps[b_idx]
            return NearestNeighborOptimizer.haversine_distance(a["lat"], a["lng"], b["lat"], b["lng"])

        depot_distances = [
            NearestNeighborOptimizer.haversine_distance(depot_lat, depot_lng, step["lat"], step["lng"])
            for step in steps
        ]

        savings = []
        for i in range(n):
            for j in range(i + 1, n):
                s = depot_distances[i] + depot_distances[j] - dist(i, j)
                savings.append((s, i, j))
        savings.sort(key=lambda item: item[0], reverse=True)

        routes_by_id: dict[int, list[int]] = {i: [i] for i in range(n)}
        node_to_route: dict[int, int] = {i: i for i in range(n)}
        next_route_id = n

        def try_merge(route_a: list[int], route_b: list[int]) -> list[int] | None:
            candidate = route_a + route_b
            candidate_steps = [steps[idx] for idx in candidate]
            if not respects_pickup_before_delivery(candidate_steps):
                return None
            return candidate

        for s, i, j in savings:
            if s <= 0:
                continue
            ri = node_to_route.get(i)
            rj = node_to_route.get(j)
            if ri is None or rj is None or ri == rj:
                continue
            route_i = routes_by_id[ri]
            route_j = routes_by_id[rj]

            merged = None
            if route_i[-1] == i and route_j[0] == j:
                merged = try_merge(route_i, route_j)
            elif route_j[-1] == j and route_i[0] == i:
                merged = try_merge(route_j, route_i)
            if merged is None:
                continue

            new_id = next_route_id
            next_route_id += 1
            del routes_by_id[ri]
            del routes_by_id[rj]
            routes_by_id[new_id] = merged
            for idx in merged:
                node_to_route[idx] = new_id

        # No vehicle-capacity constraint applies within a single mission, so force
        # any remaining route fragments together (closest endpoints first) until a
        # single tour remains.
        while len(routes_by_id) > 1:
            best: tuple[float, int, int, list[int]] | None = None
            ids = list(routes_by_id.keys())
            for a in ids:
                for b in ids:
                    if a == b:
                        continue
                    merged = try_merge(routes_by_id[a], routes_by_id[b])
                    if merged is None:
                        continue
                    d = dist(routes_by_id[a][-1], routes_by_id[b][0])
                    if best is None or d < best[0]:
                        best = (d, a, b, merged)

            if best is None:
                return None

            _, a, b, merged = best
            new_id = next_route_id
            next_route_id += 1
            del routes_by_id[a]
            del routes_by_id[b]
            routes_by_id[new_id] = merged
            for idx in merged:
                node_to_route[idx] = new_id

        final_order = next(iter(routes_by_id.values()))
        return [steps[idx] for idx in final_order]
