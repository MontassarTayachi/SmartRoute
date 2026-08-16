from __future__ import annotations

from app.algorithms.ortools_strategy import ORToolsRouteStrategy
from app.algorithms.route_strategies import SavingsRouteStrategy, respects_pickup_before_delivery


def _scattered_steps(n_deliveries=4):
    steps = []
    for i in range(n_deliveries):
        did = f"d{i}"
        plat, plng = float(i * 3), float(-i * 2)
        dlat, dlng = plat + 1.5, plng + 1.0
        steps.append({"delivery_id": did, "step_type": "pickup", "address": "", "lat": plat, "lng": plng})
        steps.append({"delivery_id": did, "step_type": "delivery", "address": "", "lat": dlat, "lng": dlng})
    return steps


class TestSavingsRouteStrategy:
    def test_empty_steps(self):
        result = SavingsRouteStrategy().optimize([])
        assert result == {"steps": [], "total_distance": 0.0, "estimated_duration": 0}

    def test_single_delivery(self):
        steps = [
            {"delivery_id": "a", "step_type": "pickup", "address": "", "lat": 0.0, "lng": 0.0},
            {"delivery_id": "a", "step_type": "delivery", "address": "", "lat": 0.0, "lng": 0.2},
        ]
        result = SavingsRouteStrategy().optimize(steps)
        assert len(result["steps"]) == 2
        assert [s["step_type"] for s in result["steps"]] == ["pickup", "delivery"]
        assert result["total_distance"] > 0
        assert respects_pickup_before_delivery(result["steps"])

    def test_respects_pickup_before_delivery_constraint(self):
        steps = _scattered_steps(6)
        result = SavingsRouteStrategy().optimize(steps, start_location=(0.0, 0.0))

        assert respects_pickup_before_delivery(result["steps"])
        assert len(result["steps"]) == len(steps)
        assert {(s["delivery_id"], s["step_type"]) for s in result["steps"]} == {
            (s["delivery_id"], s["step_type"]) for s in steps
        }
        assert result["total_distance"] > 0
        assert result["estimated_duration"] > 0

    def test_never_worse_than_nearest_neighbor_plus_refinement_baseline(self):
        import copy

        from app.algorithms.nearest_neighbor import NearestNeighborOptimizer
        from app.algorithms.route_refiner import RouteRefiner
        from app.algorithms.route_strategies import annotate_steps_for_refinement, build_distance_matrix

        steps = _scattered_steps(5)
        start_location = (1.0, -1.0)

        nn = NearestNeighborOptimizer()
        refiner = RouteRefiner(max_iterations=100)
        optimized = nn.optimize_route(copy.deepcopy(steps), start_location)
        dm = build_distance_matrix(optimized, start_location)
        annotated = annotate_steps_for_refinement(optimized, start_location)
        refined = refiner.two_opt(annotated, dm)
        refined = refiner.or_opt(refined, dm)
        for step in refined:
            step.pop("_matrix_index", None)
        baseline_distance = nn.calculate_total_distance(refined, start_location)

        result = SavingsRouteStrategy().optimize(copy.deepcopy(steps), start_location)

        assert result["total_distance"] <= baseline_distance + 1e-6


class TestORToolsRouteStrategy:
    def test_empty_steps(self):
        result = ORToolsRouteStrategy().optimize([])
        assert result == {"steps": [], "total_distance": 0.0, "estimated_duration": 0}

    def test_single_delivery(self):
        steps = [
            {"delivery_id": "a", "step_type": "pickup", "address": "", "lat": 0.0, "lng": 0.0},
            {"delivery_id": "a", "step_type": "delivery", "address": "", "lat": 0.0, "lng": 0.2},
        ]
        result = ORToolsRouteStrategy().optimize(steps)
        assert len(result["steps"]) == 2
        assert respects_pickup_before_delivery(result["steps"])

    def test_respects_pickup_before_delivery_constraint(self):
        steps = _scattered_steps(5)
        result = ORToolsRouteStrategy(parameters={"time_limit_seconds": 2}).optimize(
            steps, start_location=(0.0, 0.0)
        )

        assert respects_pickup_before_delivery(result["steps"])
        assert len(result["steps"]) == len(steps)
        assert result["total_distance"] > 0

    def test_falls_back_to_savings_when_solver_raises(self, monkeypatch):
        strategy = ORToolsRouteStrategy()
        monkeypatch.setattr(strategy, "_solve", lambda steps, start_location: (_ for _ in ()).throw(RuntimeError("boom")))

        steps = _scattered_steps(3)
        result = strategy.optimize(steps, start_location=(0.0, 0.0))

        assert respects_pickup_before_delivery(result["steps"])
        assert len(result["steps"]) == len(steps)
        assert result["total_distance"] > 0

    def test_falls_back_to_savings_when_solver_finds_no_solution(self, monkeypatch):
        strategy = ORToolsRouteStrategy()
        monkeypatch.setattr(strategy, "_solve", lambda steps, start_location: None)

        steps = _scattered_steps(3)
        result = strategy.optimize(steps, start_location=(0.0, 0.0))

        assert respects_pickup_before_delivery(result["steps"])
        assert len(result["steps"]) == len(steps)
        assert result["total_distance"] > 0

    def test_time_limit_seconds_is_read_from_parameters(self):
        strategy = ORToolsRouteStrategy(parameters={"time_limit_seconds": 42})
        assert strategy.parameters["time_limit_seconds"] == 42
