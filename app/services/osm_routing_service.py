import logging
from typing import Any

import requests


logger = logging.getLogger(__name__)


class OSMRoutingService:
    """Service for OpenStreetMap routing using OSRM API."""

    def __init__(self, osrm_base_url: str = "http://router.project-osrm.org"):
        """
        Initialize OSM routing service.

        Args:
            osrm_base_url: Base URL for OSRM server
        """
        self.osrm_base_url = osrm_base_url

    def calculate_route(
        self,
        coordinates: list[tuple[float, float]],
    ) -> dict[str, Any]:
        """
        Calculate route using OSRM API.

        Args:
            coordinates: List of (latitude, longitude) tuples in order

        Returns:
            Dictionary with route information including distance, duration, and geometry
        """
        if len(coordinates) < 2:
            logger.warning("Need at least 2 coordinates for routing")
            return {
                "distance": 0.0,
                "duration": 0,
                "geometry": "",
                "steps": [],
            }

        # Format coordinates for OSRM (longitude,latitude order)
        coord_string = ";".join([f"{lng},{lat}" for lat, lng in coordinates])

        try:
            url = f"{self.osrm_base_url}/route/v1/driving/{coord_string}"
            params = {
                "overview": "full",
                "geometries": "polyline",
                "steps": "true",
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get("code") != "Ok":
                logger.error(f"OSRM error: {data.get('code')} - {data.get('message')}")
                return self._fallback_route_calculation(coordinates)

            route = data.get("routes", [{}])[0]

            return {
                "distance": route.get("distance", 0) / 1000,  # Convert to km
                "duration": route.get("duration", 0),  # Seconds
                "geometry": route.get("geometry", ""),
                "steps": route.get("legs", []),
            }

        except requests.RequestException as e:
            logger.error(f"OSRM request failed: {e}")
            return self._fallback_route_calculation(coordinates)

    def _fallback_route_calculation(
        self, coordinates: list[tuple[float, float]]
    ) -> dict[str, Any]:
        """
        Fallback route calculation using Haversine distance when OSRM is unavailable.

        Args:
            coordinates: List of (latitude, longitude) tuples

        Returns:
            Dictionary with estimated route information
        """
        import math

        total_distance = 0.0
        for i in range(len(coordinates) - 1):
            lat1, lng1 = coordinates[i]
            lat2, lng2 = coordinates[i + 1]

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
            total_distance += R * c

        # Estimate duration (assuming 30 km/h average speed)
        avg_speed_kmh = 30.0
        estimated_duration = int((total_distance / avg_speed_kmh) * 3600)

        logger.warning(f"Using fallback route calculation: {total_distance:.2f}km")

        return {
            "distance": total_distance,
            "duration": estimated_duration,
            "geometry": "",
            "steps": [],
        }

    def calculate_matrix(
        self,
        coordinates: list[tuple[float, float]],
    ) -> list[list[float]]:
        """
        Calculate distance matrix between all coordinates.

        Args:
            coordinates: List of (latitude, longitude) tuples

        Returns:
            2D matrix of distances in kilometers
        """
        if len(coordinates) < 2:
            return [[0.0]]

        # Format coordinates for OSRM
        coord_string = ";".join([f"{lng},{lat}" for lat, lng in coordinates])

        try:
            url = f"{self.osrm_base_url}/table/v1/driving/{coord_string}"
            params = {"annotations": "distance"}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get("code") != "Ok":
                logger.error(f"OSRM table error: {data.get('code')}")
                return self._fallback_matrix_calculation(coordinates)

            distances = data.get("distances", [])
            # Convert meters to kilometers
            return [[d / 1000 for d in row] for row in distances]

        except requests.RequestException as e:
            logger.error(f"OSRM table request failed: {e}")
            return self._fallback_matrix_calculation(coordinates)

    def _fallback_matrix_calculation(
        self, coordinates: list[tuple[float, float]]
    ) -> list[list[float]]:
        """
        Fallback matrix calculation using Haversine distance.

        Args:
            coordinates: List of (latitude, longitude) tuples

        Returns:
            2D matrix of distances in kilometers
        """
        import math

        n = len(coordinates)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i != j:
                    lat1, lng1 = coordinates[i]
                    lat2, lng2 = coordinates[j]

                    R = 6371
                    lat1_rad = math.radians(lat1)
                    lat2_rad = math.radians(lat2)
                    delta_lat = math.radians(lat2 - lat1)
                    delta_lng = math.radians(lng2 - lng1)

                    a = (
                        math.sin(delta_lat / 2) ** 2
                        + math.cos(lat1_rad)
                        * math.cos(lat2_rad)
                        * math.sin(delta_lng / 2) ** 2
                    )
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    matrix[i][j] = R * c

        return matrix
