from app.services.driver_assignment_service import DriverAssignmentService


def test_assign_drivers_to_regions_can_leave_regions_without_a_driver():
    """
    Baseline: with more regions than drivers, assign_drivers_to_regions only ever
    puts a driver in their single nearest region, so some regions legitimately end
    up empty. redistribute_orphaned_region_deliveries is what's responsible for
    making sure those regions' deliveries aren't dropped (see the next test).
    """
    service = DriverAssignmentService()
    drivers = [{"id": "drv-1", "current_lat": 0.0, "current_lng": 0.0}]
    region_centers = [(0.0, 0.0), (10.0, 10.0), (20.0, 20.0)]

    region_drivers = service.assign_drivers_to_regions(drivers, region_centers)

    assert region_drivers[0] == drivers
    assert region_drivers[1] == []
    assert region_drivers[2] == []


def test_redistribute_orphaned_region_deliveries_merges_into_nearest_served_region():
    """
    Reproduces the reported bug: increasing the number of regions (n_clusters)
    while the driver count stays fixed used to shrink the number of deliveries
    that got assigned, because regions with zero drivers were simply skipped.
    Deliveries from a driver-less region must now be folded into the nearest
    region that does have a driver instead of being lost.
    """
    service = DriverAssignmentService()
    region_centers = [(0.0, 0.0), (10.0, 10.0), (20.0, 20.0)]
    region_deliveries = {
        0: [{"id": "d1"}],
        1: [{"id": "d2"}, {"id": "d3"}],
        2: [{"id": "d4"}],
    }
    # Only region 0 has a driver (mirrors assign_drivers_to_regions above).
    region_drivers = {0: [{"id": "drv-1"}], 1: [], 2: []}

    merged = service.redistribute_orphaned_region_deliveries(
        region_deliveries, region_drivers, region_centers
    )

    assert set(merged.keys()) == {0}
    merged_ids = {d["id"] for d in merged[0]}
    assert merged_ids == {"d1", "d2", "d3", "d4"}


def test_redistribute_orphaned_region_deliveries_picks_geographically_nearest_target():
    service = DriverAssignmentService()
    region_centers = [(0.0, 0.0), (1.0, 1.0), (50.0, 50.0)]
    region_deliveries = {
        0: [{"id": "d1"}],
        1: [{"id": "d2"}],
        2: [{"id": "orphan"}],
    }
    # Regions 0 and 1 are both served; region 2 (far away) has no driver and
    # should merge into whichever served region is geographically closest to it.
    region_drivers = {0: [{"id": "drv-near-0"}], 1: [{"id": "drv-near-1"}], 2: []}

    merged = service.redistribute_orphaned_region_deliveries(
        region_deliveries, region_drivers, region_centers
    )

    assert set(merged.keys()) == {0, 1}
    assert {d["id"] for d in merged[1]} == {"d2", "orphan"}
    assert {d["id"] for d in merged[0]} == {"d1"}
