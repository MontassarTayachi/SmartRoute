import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


class DriverAssignmentService:
    """Service for assigning drivers to geographic regions."""

    @staticmethod
    def haversine_distance(
        lat1: float, lng1: float, lat2: float, lng2: float
    ) -> float:
        """
        Calculate the Haversine distance between two coordinates in kilometers.

        Args:
            lat1, lng1: Latitude and longitude of first point
            lat2, lng2: Latitude and longitude of second point

        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def assign_drivers_to_regions(
        self,
        drivers: list[dict[str, Any]],
        region_centers: list[tuple[float, float]],
    ) -> dict[int, list[dict[str, Any]]]:
        """
        Assign drivers to the nearest regions based on their current location.

        Args:
            drivers: List of drivers with current location (lat, lng)
            region_centers: List of (latitude, longitude) tuples for region centers

        Returns:
            Dictionary mapping region_id to list of assigned drivers
        """
        if not drivers or not region_centers:
            logger.warning("No drivers or regions provided for assignment")
            return {}

        # Initialize regions
        region_assignments: dict[int, list[dict[str, Any]]] = {
            i: [] for i in range(len(region_centers))
        }

        for driver in drivers:
            # Get driver's current location (default to first region center if not available)
            driver_lat = driver.get("current_lat", region_centers[0][0])
            driver_lng = driver.get("current_lng", region_centers[0][1])

            # Find nearest region
            nearest_region = 0
            min_distance = float("inf")

            for region_id, (center_lat, center_lng) in enumerate(region_centers):
                distance = self.haversine_distance(
                    driver_lat, driver_lng, center_lat, center_lng
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_region = region_id

            region_assignments[nearest_region].append(driver)

        logger.info(f"Assigned {len(drivers)} drivers to {len(region_assignments)} regions")
        return region_assignments

    def redistribute_orphaned_region_deliveries(
        self,
        region_deliveries: dict[int, list[dict[str, Any]]],
        region_drivers: dict[int, list[dict[str, Any]]],
        region_centers: list[tuple[float, float]],
    ) -> dict[int, list[dict[str, Any]]]:
        """
        Fold deliveries from regions with zero assigned drivers into the nearest
        region that does have a driver, instead of dropping them.

        Both assign_drivers_to_regions and optimize_driver_assignment put each
        driver in at most one region, so whenever n_clusters exceeds the number
        of drivers, some regions are guaranteed to end up with an empty driver
        list. Callers used to just `continue` past those regions (see
        MissionService._build_mission_drafts and the /assign route), which meant
        raising the region count silently shrank the number of deliveries that
        got assigned. Merging into the nearest served region keeps every
        delivery covered without double-booking a driver across two separate
        mission drafts for the same day (which assigning the same driver to
        multiple regions directly would cause, since capacity is computed
        independently per region).
        """
        driven_region_ids = [
            region_id for region_id, drivers in region_drivers.items() if drivers
        ]
        if not driven_region_ids:
            return region_deliveries

        merged: dict[int, list[dict[str, Any]]] = {
            region_id: list(deliveries)
            for region_id, deliveries in region_deliveries.items()
            if region_id in driven_region_ids
        }

        for region_id, deliveries in region_deliveries.items():
            if region_id in driven_region_ids or not deliveries:
                continue

            center_lat, center_lng = region_centers[region_id]
            nearest_driven_region = min(
                driven_region_ids,
                key=lambda candidate_id: self.haversine_distance(
                    center_lat,
                    center_lng,
                    region_centers[candidate_id][0],
                    region_centers[candidate_id][1],
                ),
            )
            merged.setdefault(nearest_driven_region, []).extend(deliveries)
            logger.info(
                f"Region {region_id} had {len(deliveries)} deliveries but no driver; "
                f"merged into region {nearest_driven_region}"
            )

        return merged

    def optimize_driver_assignment(
        self,
        drivers: list[dict[str, Any]],
        region_centers: list[tuple[float, float]],
        region_deliveries: dict[int, list[dict[str, Any]]],
    ) -> dict[int, list[dict[str, Any]]]:
        """
        Optimize driver assignment considering both distance and workload.

        Used exclusively by the POST /api/missions/assign route (manual/on-demand
        assignment), where prioritizing the busiest regions first is desirable when
        drivers are scarce. The daily batch pipeline (MissionService.generate_missions_for_date)
        intentionally uses the simpler assign_drivers_to_regions (nearest-region-only)
        instead — see the comment in app/routers/missions.py's assign_deliveries route.

        Args:
            drivers: List of available drivers
            region_centers: List of region center coordinates
            region_deliveries: Dictionary mapping region_id to deliveries

        Returns:
            Optimized dictionary mapping region_id to assigned drivers
        """
        if not drivers:
            return {}

        # Calculate workload for each region (number of deliveries)
        region_workloads = {
            region_id: len(deliveries) for region_id, deliveries in region_deliveries.items()
        }

        # Sort regions by workload (descending)
        sorted_regions = sorted(
            region_workloads.items(), key=lambda x: x[1], reverse=True
        )

        # Initialize assignments
        region_assignments: dict[int, list[dict[str, Any]]] = {
            i: [] for i in range(len(region_centers))
        }

        # Assign drivers to regions with highest workload first
        for region_id, _ in sorted_regions:
            if not drivers:
                break

            # Find the driver closest to this region
            region_center = region_centers[region_id]
            nearest_driver = None
            min_distance = float("inf")

            for driver in drivers:
                driver_lat = driver.get("current_lat", region_center[0])
                driver_lng = driver.get("current_lng", region_center[1])
                distance = self.haversine_distance(
                    driver_lat, driver_lng, region_center[0], region_center[1]
                )

                if distance < min_distance:
                    min_distance = distance
                    nearest_driver = driver

            if nearest_driver:
                region_assignments[region_id].append(nearest_driver)
                drivers.remove(nearest_driver)

        # Assign remaining drivers to nearest regions
        for driver in drivers:
            driver_lat = driver.get("current_lat", region_centers[0][0])
            driver_lng = driver.get("current_lng", region_centers[0][1])

            nearest_region = 0
            min_distance = float("inf")

            for region_id, (center_lat, center_lng) in enumerate(region_centers):
                distance = self.haversine_distance(
                    driver_lat, driver_lng, center_lat, center_lng
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_region = region_id

            region_assignments[nearest_region].append(driver)

        return region_assignments
