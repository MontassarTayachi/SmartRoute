import pytest
from app.algorithms.nearest_neighbor import NearestNeighborOptimizer


def test_haversine_distance():
    """Test Haversine distance calculation."""
    optimizer = NearestNeighborOptimizer()

    # Distance between Paris and London (approximately 344 km)
    distance = optimizer.haversine_distance(48.8566, 2.3522, 51.5074, -0.1278)
    assert 340 < distance < 350


def test_haversine_distance_same_point():
    """Test Haversine distance for same point."""
    optimizer = NearestNeighborOptimizer()
    distance = optimizer.haversine_distance(48.8566, 2.3522, 48.8566, 2.3522)
    assert distance == 0.0


def test_optimize_route_empty():
    """Test route optimization with empty steps."""
    optimizer = NearestNeighborOptimizer()
    result = optimizer.optimize_route([])
    assert result == []


def test_optimize_route_single_step():
    """Test route optimization with single step."""
    optimizer = NearestNeighborOptimizer()
    steps = [
        {"delivery_id": "1", "step_type": "pickup", "lat": 48.8566, "lng": 2.3522}
    ]
    result = optimizer.optimize_route(steps)
    assert len(result) == 1


def test_optimize_route_with_pickup_delivery_constraint():
    """Test route optimization respecting pickup-before-delivery constraint."""
    optimizer = NearestNeighborOptimizer()

    steps = [
        {
            "delivery_id": "1",
            "step_type": "pickup",
            "address": "Pickup 1",
            "lat": 48.8566,
            "lng": 2.3522,
        },
        {
            "delivery_id": "1",
            "step_type": "delivery",
            "address": "Delivery 1",
            "lat": 48.8666,
            "lng": 2.3722,
        },
        {
            "delivery_id": "2",
            "step_type": "pickup",
            "address": "Pickup 2",
            "lat": 48.8766,
            "lng": 2.3822,
        },
        {
            "delivery_id": "2",
            "step_type": "delivery",
            "address": "Delivery 2",
            "lat": 48.8866,
            "lng": 2.3922,
        },
    ]

    result = optimizer.optimize_route(steps)

    # Verify pickup comes before delivery for each delivery
    pickup_orders = {}
    for step in result:
        if step["step_type"] == "pickup":
            pickup_orders[step["delivery_id"]] = result.index(step)
        elif step["step_type"] == "delivery":
            pickup_order = pickup_orders.get(step["delivery_id"])
            assert pickup_order is not None
            assert pickup_order < result.index(step)


def test_calculate_total_distance():
    """Test total distance calculation."""
    optimizer = NearestNeighborOptimizer()

    steps = [
        {"lat": 48.8566, "lng": 2.3522},
        {"lat": 48.8666, "lng": 2.3722},
    ]

    distance = optimizer.calculate_total_distance(steps)
    assert distance > 0


def test_calculate_total_distance_empty():
    """Test total distance calculation with empty steps."""
    optimizer = NearestNeighborOptimizer()
    distance = optimizer.calculate_total_distance([])
    assert distance == 0.0


def test_calculate_total_distance_with_start_location():
    """Test total distance calculation with custom start location."""
    optimizer = NearestNeighborOptimizer()

    steps = [
        {"lat": 48.8566, "lng": 2.3522},
    ]

    start_location = (48.8466, 2.3422)
    distance = optimizer.calculate_total_distance(steps, start_location)
    assert distance > 0
