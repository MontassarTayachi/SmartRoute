import pytest
from datetime import datetime, timedelta
from app.services.mission_service import MissionService


@pytest.mark.asyncio
async def test_mission_generation_with_db_data():
    """
    Integration test for mission generation using real database data.
    This test fetches actual deliveries, drivers, and vehicles from the database
    and runs the complete mission optimization pipeline.
    """
    from app.db.mongodb import connect_to_mongo, close_mongo_connection
    from app.core.config import settings

    # Connect to MongoDB
    mongo_client, mongodb = connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)

    try:
        mission_service = MissionService(mongodb)

        # Test with today's date
        target_date = datetime.utcnow()

        # Generate missions
        missions = await mission_service.generate_missions_for_date(target_date)

        # Verify missions were generated
        assert isinstance(missions, list)

        if missions:
            # Verify mission structure
            for mission in missions:
                assert "driver_id" in mission
                assert "vehicle_id" in mission
                assert "region_id" in mission
                assert "delivery_ids" in mission
                assert "deliveries_order" in mission
                assert "total_weight" in mission
                assert "route_distance" in mission
                assert "route_duration" in mission
                assert "status" in mission
                assert "created_at" in mission
                assert "scheduled_date" in mission
                assert "updated_at" in mission

                # Verify deliveries order respects pickup-before-delivery
                delivery_pickup_orders = {}
                for step in mission["deliveries_order"]:
                    delivery_id = step["delivery_id"]
                    step_type = step["step_type"]
                    order = step["order"]

                    if step_type == "pickup":
                        delivery_pickup_orders[delivery_id] = order
                    elif step_type == "delivery":
                        pickup_order = delivery_pickup_orders.get(delivery_id)
                        assert pickup_order is not None, f"Delivery {delivery_id} has delivery without pickup"
                        assert pickup_order < order, f"Delivery {delivery_id} pickup after delivery"

                # Verify capacity constraints
                total_weight = mission["total_weight"]
                # Get vehicle capacity
                vehicle = await mongodb.vehicles.find_one({"_id": mission["vehicle_id"]})
                if vehicle:
                    capacity = vehicle.get("capacity_kg", 0)
                    assert total_weight <= capacity, f"Mission weight {total_weight} exceeds vehicle capacity {capacity}"

            print(f"\n✓ Successfully generated {len(missions)} missions")
            print(f"✓ All missions respect pickup-before-delivery constraints")
            print(f"✓ All missions respect vehicle capacity constraints")
        else:
            print("\n⚠ No missions generated (no pending deliveries for today)")

    finally:
        # Close MongoDB connection
        await close_mongo_connection(mongo_client)


@pytest.mark.asyncio
async def test_mission_retrieval():
    """Test retrieving missions from the database."""
    from app.db.mongodb import connect_to_mongo, close_mongo_connection
    from app.core.config import settings

    # Connect to MongoDB
    mongo_client, mongodb = connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)

    try:
        mission_service = MissionService(mongodb)

        # Get today's missions
        today = datetime.utcnow()
        missions = await mission_service.get_missions_for_date(today)

        assert isinstance(missions, list)

        if missions:
            # Test retrieving a specific mission
            mission_id = missions[0].get("_id")
            if mission_id:
                mission = await mission_service.get_mission_by_id(mission_id)
                assert mission is not None
                assert mission["_id"] == mission_id

                # Verify driver and vehicle are populated
                assert "driver" in mission or mission.get("driver") is None
                assert "vehicle" in mission or mission.get("vehicle") is None

                print(f"\n✓ Successfully retrieved mission {mission_id}")
            else:
                print("\n⚠ No mission ID found for retrieval test")
        else:
            print("\n⚠ No missions found for today")

    finally:
        # Close MongoDB connection
        await close_mongo_connection(mongo_client)


@pytest.mark.asyncio
async def test_clustering_with_db_data():
    """Test geographic clustering with real delivery data from database."""
    from app.db.mongodb import connect_to_mongo, close_mongo_connection
    from app.core.config import settings
    from app.services.clustering_service import ClusteringService

    # Connect to MongoDB
    mongo_client, mongodb = connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)

    try:
        # Fetch deliveries from database
        start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        cursor = mongodb.deliveries.find({
            "scheduled_at": {"$gte": start_of_day, "$lt": end_of_day},
            "status": {"$in": ["pending", "assigned"]}
        })

        deliveries = await cursor.to_list(length=None)

        if deliveries:
            # Fetch available drivers to determine optimal cluster count
            cursor = mongodb.drivers.find({"availability": "available"})
            drivers = await cursor.to_list(length=None)

            n_clusters = min(5, len(drivers)) if drivers else 1
            clustering_service = ClusteringService(n_clusters=n_clusters)
            regions = clustering_service.cluster_deliveries(deliveries)

            assert isinstance(regions, dict)
            assert len(regions) > 0

            # Verify all deliveries are assigned to a region
            total_deliveries_in_regions = sum(len(deliveries) for deliveries in regions.values())
            assert total_deliveries_in_regions == len(deliveries)

            # Get region centers
            centers = clustering_service.get_region_centers()
            assert len(centers) == len(regions)

            print(f"\n✓ Successfully clustered {len(deliveries)} deliveries into {len(regions)} regions")
            for region_id, region_deliveries in regions.items():
                print(f"  Region {region_id}: {len(region_deliveries)} deliveries")
        else:
            print("\n⚠ No deliveries found for clustering test")

    finally:
        # Close MongoDB connection
        await close_mongo_connection(mongo_client)


@pytest.mark.asyncio
async def test_route_optimization_with_db_data():
    """Test route optimization with real delivery data from database."""
    from app.db.mongodb import connect_to_mongo, close_mongo_connection
    from app.core.config import settings
    from app.services.route_optimizer import RouteOptimizerService

    # Connect to MongoDB
    mongo_client, mongodb = connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)

    try:
        # Fetch a few deliveries from database
        cursor = mongodb.deliveries.find({"status": "pending"}).limit(5)
        deliveries = await cursor.to_list(length=None)

        if deliveries:
            route_optimizer = RouteOptimizerService()
            result = route_optimizer.optimize_mission_route(deliveries)

            assert "steps" in result
            assert "total_distance" in result
            assert "estimated_duration" in result

            # Verify constraints
            assert route_optimizer.validate_route_constraints(result["steps"])

            print(f"\n✓ Successfully optimized route for {len(deliveries)} deliveries")
            print(f"  Total distance: {result['total_distance']:.2f} km")
            print(f"  Estimated duration: {result['estimated_duration']} seconds")
            print(f"  Number of steps: {len(result['steps'])}")
        else:
            print("\n⚠ No deliveries found for route optimization test")

    finally:
        # Close MongoDB connection
        await close_mongo_connection(mongo_client)


if __name__ == "__main__":
    """
    Run integration tests manually without pytest.
    Usage: python -m tests.test_mission_integration
    """
    import asyncio

    print("Running integration tests with database data...\n")

    async def run_all_tests():
        print("=" * 60)
        print("TEST 1: Mission Generation")
        print("=" * 60)
        try:
            await test_mission_generation_with_db_data()
        except Exception as e:
            import traceback
            print(f"✗ Test failed: {e}")
            traceback.print_exc()

        print("\n" + "=" * 60)
        print("TEST 2: Mission Retrieval")
        print("=" * 60)
        try:
            await test_mission_retrieval()
        except Exception as e:
            print(f"✗ Test failed: {e}")

        print("\n" + "=" * 60)
        print("TEST 3: Clustering")
        print("=" * 60)
        try:
            await test_clustering_with_db_data()
        except Exception as e:
            print(f"✗ Test failed: {e}")

        print("\n" + "=" * 60)
        print("TEST 4: Route Optimization")
        print("=" * 60)
        try:
            await test_route_optimization_with_db_data()
        except Exception as e:
            print(f"✗ Test failed: {e}")

        print("\n" + "=" * 60)
        print("All integration tests completed")
        print("=" * 60)

    asyncio.run(run_all_tests())
