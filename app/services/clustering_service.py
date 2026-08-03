import logging
from typing import Any

import numpy as np

from app.algorithms.kmeans import KMeansClusterer
from app.services.optimization_settings_service import OptimizationSettingsService


logger = logging.getLogger(__name__)


class ClusteringService:
    """Service for geographic clustering of deliveries."""

    def __init__(self, n_clusters: int = 5, db=None, driver_count: int | None = None):
        """
        Initialize clustering service.

        Args:
            n_clusters: Number of clusters (regions) to create
        """
        self.db = db
        self.driver_count = driver_count
        self.n_clusters = self._resolve_n_clusters(n_clusters)
        self.clusterer = KMeansClusterer(n_clusters=self.n_clusters)

    def _resolve_n_clusters(self, fallback_n_clusters: int) -> int:
        if self.db is None:
            return fallback_n_clusters

        settings_service = OptimizationSettingsService(self.db)
        region_settings = settings_service.get_region_settings()
        if not region_settings:
            return fallback_n_clusters

        configured_n_clusters = int(region_settings.get("n_clusters", fallback_n_clusters))
        mode = region_settings.get("mode", "fixe")

        if mode == "auto" and self.driver_count:
            return max(1, min(configured_n_clusters, self.driver_count))

        return max(1, configured_n_clusters)

    def cluster_deliveries(self, deliveries: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
        """
        Cluster deliveries into geographic regions.

        Args:
            deliveries: List of delivery dictionaries with pickup/dropoff coordinates

        Returns:
            Dictionary mapping region_id to list of deliveries in that region
        """
        if not deliveries:
            logger.warning("No deliveries provided for clustering")
            return {}

        # Calculate centroid for each delivery
        delivery_centroids = []
        for delivery in deliveries:
            pickup_lat = delivery.get("pickup_address_lat")
            pickup_lng = delivery.get("pickup_address_lng")
            dropoff_lat = delivery.get("dropoff_address_lat")
            dropoff_lng = delivery.get("dropoff_address_lng")

            if (
                pickup_lat is not None
                and pickup_lng is not None
                and dropoff_lat is not None
                and dropoff_lng is not None
            ):
                centroid_lat = (pickup_lat + dropoff_lat) / 2
                centroid_lng = (pickup_lng + dropoff_lng) / 2
                delivery_centroids.append((centroid_lat, centroid_lng))
            else:
                logger.warning(f"Delivery {delivery.get('id')} missing coordinates")
                delivery_centroids.append((0.0, 0.0))

        # Perform clustering
        labels = self.clusterer.fit_predict(delivery_centroids)

        # Group deliveries by region
        regions: dict[int, list[dict[str, Any]]] = {}
        for delivery, label in zip(deliveries, labels):
            if label not in regions:
                regions[label] = []
            regions[label].append(delivery)

        self._persist_region_geometry(delivery_centroids, labels)

        logger.info(f"Clustered {len(deliveries)} deliveries into {len(regions)} regions")
        return regions

    def get_region_centers(self) -> list[tuple[float, float]]:
        """
        Get the center coordinates of each region.

        Returns:
            List of (latitude, longitude) tuples for region centers
        """
        return self.clusterer.get_cluster_centers()

    def assign_delivery_to_region(
        self, delivery: dict[str, Any]
    ) -> int:
        """
        Assign a new delivery to the nearest existing region.

        Args:
            delivery: Delivery dictionary with pickup/dropoff coordinates

        Returns:
            Region ID for the delivery
        """
        pickup_lat = delivery.get("pickup_address_lat")
        pickup_lng = delivery.get("pickup_address_lng")
        dropoff_lat = delivery.get("dropoff_address_lat")
        dropoff_lng = delivery.get("dropoff_address_lng")

        if (
            pickup_lat is not None
            and pickup_lng is not None
            and dropoff_lat is not None
            and dropoff_lng is not None
        ):
            centroid_lat = (pickup_lat + dropoff_lat) / 2
            centroid_lng = (pickup_lng + dropoff_lng) / 2
            centroid = (centroid_lat, centroid_lng)

            labels = self.clusterer.assign_to_nearest_cluster([centroid])
            return labels[0] if labels else 0

        return 0

    @staticmethod
    def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        earth_radius_km = 6371.0
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lng = np.radians(lng2 - lng1)

        a = (
            np.sin(delta_lat / 2) ** 2
            + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lng / 2) ** 2
        )
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return float(earth_radius_km * c)

    def _persist_region_geometry(
        self,
        delivery_centroids: list[tuple[float, float]],
        labels: list[int],
    ) -> None:
        if self.db is None:
            return

        settings_service = OptimizationSettingsService(self.db)
        cluster_centers = self.clusterer.get_cluster_centers()

        for region_id, (center_lat, center_lng) in enumerate(cluster_centers):
            region_points = [point for point, label in zip(delivery_centroids, labels) if label == region_id]
            if not region_points:
                continue

            distances = [
                self._haversine_distance(center_lat, center_lng, point_lat, point_lng)
                for point_lat, point_lng in region_points
            ]
            radius_km = float(np.percentile(distances, 90)) if distances else 0.0
            settings_service.save_region_geometry(
                region_id=region_id,
                center_lat=float(center_lat),
                center_lng=float(center_lng),
                radius_km=radius_km,
            )
