from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


class RouteRefiner:
    """Local route refinement using 2-opt and Or-opt moves."""

    def __init__(self, max_iterations: int = 100):
        self.max_iterations = max_iterations

    def two_opt(self, route: list[dict[str, Any]], distance_matrix: list[list[float]]) -> list[dict[str, Any]]:
        """Improve a route by reversing segments when it reduces total distance."""
        return self._search(route, distance_matrix, move_type="two_opt")

    def or_opt(self, route: list[dict[str, Any]], distance_matrix: list[list[float]]) -> list[dict[str, Any]]:
        """Improve a route by relocating short segments when it reduces total distance."""
        return self._search(route, distance_matrix, move_type="or_opt")

    def _search(
        self,
        route: list[dict[str, Any]],
        distance_matrix: list[list[float]],
        *,
        move_type: str,
    ) -> list[dict[str, Any]]:
        if len(route) < 3:
            return route.copy()

        best_route = route.copy()
        best_cost = self._route_cost(best_route, distance_matrix)

        for _ in range(self.max_iterations):
            improved = False

            if move_type == "two_opt":
                improved, best_route, best_cost = self._run_two_opt_pass(best_route, distance_matrix, best_cost)
            else:
                improved, best_route, best_cost = self._run_or_opt_pass(best_route, distance_matrix, best_cost)

            if not improved:
                break

        return best_route

    def _run_two_opt_pass(
        self,
        route: list[dict[str, Any]],
        distance_matrix: list[list[float]],
        current_best_cost: float,
    ) -> tuple[bool, list[dict[str, Any]], float]:
        best_route = route
        best_cost = current_best_cost

        for start_index in range(1, len(route) - 1):
            for end_index in range(start_index + 1, len(route)):
                candidate = route[:start_index] + list(reversed(route[start_index : end_index + 1])) + route[end_index + 1 :]
                if not self._is_valid_route(candidate):
                    continue

                candidate_cost = self._route_cost(candidate, distance_matrix)
                if candidate_cost + 1e-9 < best_cost:
                    logger.debug(
                        "2-opt improvement accepted: %.4f -> %.4f",
                        best_cost,
                        candidate_cost,
                    )
                    return True, candidate, candidate_cost

        return False, best_route, best_cost

    def _run_or_opt_pass(
        self,
        route: list[dict[str, Any]],
        distance_matrix: list[list[float]],
        current_best_cost: float,
    ) -> tuple[bool, list[dict[str, Any]], float]:
        best_route = route
        best_cost = current_best_cost
        max_segment_length = min(3, len(route) - 1)

        for segment_length in range(1, max_segment_length + 1):
            for start_index in range(0, len(route) - segment_length + 1):
                segment = route[start_index : start_index + segment_length]
                remainder = route[:start_index] + route[start_index + segment_length :]

                for insert_index in range(0, len(remainder) + 1):
                    if insert_index == start_index:
                        continue

                    candidate = remainder[:insert_index] + segment + remainder[insert_index:]
                    if len(candidate) != len(route):
                        continue
                    if not self._is_valid_route(candidate):
                        continue

                    candidate_cost = self._route_cost(candidate, distance_matrix)
                    if candidate_cost + 1e-9 < best_cost:
                        logger.debug(
                            "Or-opt improvement accepted: %.4f -> %.4f",
                            best_cost,
                            candidate_cost,
                        )
                        return True, candidate, candidate_cost

        return False, best_route, best_cost

    def _route_cost(self, route: list[dict[str, Any]], distance_matrix: list[list[float]]) -> float:
        if not route:
            return 0.0

        offset = len(distance_matrix) - len(route)
        if offset not in {0, 1}:
            raise ValueError("Distance matrix size must match route length or include one start node.")

        indices: list[int] = []
        for index, step in enumerate(route):
            matrix_index = step.get("_matrix_index")
            if matrix_index is None:
                matrix_index = index + offset
            indices.append(int(matrix_index))

        total = 0.0

        if offset == 1:
            total += distance_matrix[0][indices[0]]

        previous_index = indices[0]
        for current_index in indices[1:]:
            total += distance_matrix[previous_index][current_index]
            previous_index = current_index

        return total

    def _is_valid_route(self, route: list[dict[str, Any]]) -> bool:
        pickup_positions: dict[Any, int] = {}

        for position, step in enumerate(route):
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