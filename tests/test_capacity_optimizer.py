import pytest
from app.algorithms.capacity_optimizer import CapacityOptimizer


def test_assign_deliveries_to_vehicles_basic():
    """Test basic delivery assignment to vehicles."""
    optimizer = CapacityOptimizer()

    deliveries = [
        {"id": "1", "weight_kg": 100},
        {"id": "2", "weight_kg": 150},
        {"id": "3", "weight_kg": 200},
    ]

    vehicles = [
        {"id": "v1", "capacity_kg": 500},
        {"id": "v2", "capacity_kg": 500},
    ]

    drivers = [
        {"id": "d1", "assigned_vehicle_id": "v1"},
        {"id": "d2", "assigned_vehicle_id": "v2"},
    ]

    assignments = optimizer.assign_deliveries_to_vehicles(deliveries, vehicles, drivers)

    assert len(assignments) > 0
    assert all("driver_id" in a for a in assignments)
    assert all("vehicle_id" in a for a in assignments)
    assert all("deliveries" in a for a in assignments)


def test_assign_deliveries_empty():
    """Test assignment with empty deliveries."""
    optimizer = CapacityOptimizer()

    assignments = optimizer.assign_deliveries_to_vehicles([], [], [])
    assert assignments == []


def test_assign_deliveries_no_vehicles():
    """Test assignment with no vehicles."""
    optimizer = CapacityOptimizer()

    deliveries = [{"id": "1", "weight_kg": 100}]
    drivers = [{"id": "d1"}]

    assignments = optimizer.assign_deliveries_to_vehicles(deliveries, [], drivers)
    assert assignments == []


def test_assign_deliveries_capacity_constraint():
    """Test that capacity constraints are respected."""
    optimizer = CapacityOptimizer()

    deliveries = [
        {"id": "1", "weight_kg": 300},
        {"id": "2", "weight_kg": 400},
    ]

    vehicles = [
        {"id": "v1", "capacity_kg": 500},
    ]

    drivers = [
        {"id": "d1", "assigned_vehicle_id": "v1"},
    ]

    assignments = optimizer.assign_deliveries_to_vehicles(deliveries, vehicles, drivers)

    # Total weight should not exceed capacity
    for assignment in assignments:
        total_weight = assignment["total_weight"]
        vehicle_capacity = assignment["vehicle"]["capacity_kg"]
        assert total_weight <= vehicle_capacity


def test_distribute_deliveries_by_region():
    """Test distribution of deliveries within a region."""
    optimizer = CapacityOptimizer()

    region_deliveries = [
        {"id": "1", "weight_kg": 100},
        {"id": "2", "weight_kg": 150},
    ]

    drivers_in_region = [
        {"id": "d1", "assigned_vehicle_id": "v1"},
    ]

    vehicles = [
        {"id": "v1", "capacity_kg": 500},
    ]

    assignments = optimizer.distribute_deliveries_by_region(
        region_deliveries, drivers_in_region, vehicles
    )

    assert len(assignments) > 0


def test_distribute_deliveries_empty_region():
    """Test distribution with empty region deliveries."""
    optimizer = CapacityOptimizer()

    assignments = optimizer.distribute_deliveries_by_region([], [], [])
    assert assignments == []


def test_validate_capacity_valid():
    """Test capacity validation for valid assignment."""
    optimizer = CapacityOptimizer()

    deliveries = [
        {"id": "1", "weight_kg": 100},
        {"id": "2", "weight_kg": 150},
    ]

    vehicle = {"capacity_kg": 500}

    is_valid = optimizer.validate_capacity(deliveries, vehicle)
    assert is_valid is True


def test_validate_capacity_invalid():
    """Test capacity validation for invalid assignment."""
    optimizer = CapacityOptimizer()

    deliveries = [
        {"id": "1", "weight_kg": 300},
        {"id": "2", "weight_kg": 400},
    ]

    vehicle = {"capacity_kg": 500}

    is_valid = optimizer.validate_capacity(deliveries, vehicle)
    assert is_valid is False


def test_validate_capacity_empty_deliveries():
    """Test capacity validation with empty deliveries."""
    optimizer = CapacityOptimizer()

    vehicle = {"capacity_kg": 500}

    is_valid = optimizer.validate_capacity([], vehicle)
    assert is_valid is True
