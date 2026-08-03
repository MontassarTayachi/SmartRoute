from app.algorithms.route_refiner import RouteRefiner


def _build_matrix(values: list[list[float]]) -> list[list[float]]:
    return values


def test_two_opt_corrects_crossing_route():
    refiner = RouteRefiner(max_iterations=10)

    route = [
        {"delivery_id": "a", "step_type": "pickup", "lat": 0.0, "lng": 0.0, "_matrix_index": 0},
        {"delivery_id": "b", "step_type": "pickup", "lat": 0.0, "lng": 10.0, "_matrix_index": 1},
        {"delivery_id": "a", "step_type": "delivery", "lat": 0.0, "lng": 11.0, "_matrix_index": 2},
        {"delivery_id": "b", "step_type": "delivery", "lat": 0.0, "lng": 1.0, "_matrix_index": 3},
    ]

    distance_matrix = _build_matrix(
        [
            [0.0, 10.0, 1.0, 10.0],
            [10.0, 0.0, 1.0, 1.0],
            [1.0, 1.0, 0.0, 10.0],
            [10.0, 1.0, 10.0, 0.0],
        ]
    )

    optimized = refiner.two_opt(route, distance_matrix)

    assert [step["delivery_id"] + ":" + step["step_type"] for step in optimized] == [
        "a:pickup",
        "b:pickup",
        "b:delivery",
        "a:delivery",
    ]


def test_or_opt_preserves_already_optimal_route():
    refiner = RouteRefiner(max_iterations=10)

    route = [
        {"delivery_id": "a", "step_type": "pickup", "lat": 0.0, "lng": 0.0, "_matrix_index": 0},
        {"delivery_id": "a", "step_type": "delivery", "lat": 0.0, "lng": 1.0, "_matrix_index": 1},
        {"delivery_id": "b", "step_type": "pickup", "lat": 0.0, "lng": 2.0, "_matrix_index": 2},
        {"delivery_id": "b", "step_type": "delivery", "lat": 0.0, "lng": 3.0, "_matrix_index": 3},
    ]

    distance_matrix = _build_matrix(
        [
            [0.0, 1.0, 2.0, 3.0],
            [1.0, 0.0, 1.0, 2.0],
            [2.0, 1.0, 0.0, 1.0],
            [3.0, 2.0, 1.0, 0.0],
        ]
    )

    optimized = refiner.or_opt(route, distance_matrix)

    assert optimized == route


def test_route_refiner_rejects_pickup_delivery_violation():
    refiner = RouteRefiner(max_iterations=10)

    route = [
        {"delivery_id": "a", "step_type": "pickup", "lat": 0.0, "lng": 0.0, "_matrix_index": 0},
        {"delivery_id": "b", "step_type": "pickup", "lat": 0.0, "lng": 10.0, "_matrix_index": 1},
        {"delivery_id": "b", "step_type": "delivery", "lat": 0.0, "lng": 1.0, "_matrix_index": 2},
        {"delivery_id": "a", "step_type": "delivery", "lat": 0.0, "lng": 11.0, "_matrix_index": 3},
    ]

    distance_matrix = _build_matrix(
        [
            [0.0, 10.0, 1.0, 10.0],
            [10.0, 0.0, 1.0, 1.0],
            [1.0, 1.0, 0.0, 10.0],
            [10.0, 100.0, 100.0, 0.0],
        ]
    )

    optimized = refiner.two_opt(route, distance_matrix)

    assert optimized == route