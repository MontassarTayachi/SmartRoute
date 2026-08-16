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
        # A fresh KMeansClusterer is created per ClusteringService instance, and callers
        # (MissionService.generate_missions_for_date, the /assign and /test-generate
        # routes) all instantiate a new ClusteringService per request/date rather than
        # sharing one. Do not change this to a shared/cached instance without also
        # resetting KMeansClusterer.n_clusters between uses (see kmeans.py fit_predict).
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

    def cluster_deliveries(
        self, deliveries: list[dict[str, Any]]
    ) -> tuple[dict[int, list[dict[str, Any]]], list[dict[str, Any]]]:
        """
        Cluster deliveries into geographic regions.

        Args:
            deliveries: List of delivery dictionaries with pickup/dropoff coordinates

        Returns:
            Tuple of:
            - Dictionary mapping region_id to list of deliveries in that region
            - List of deliveries excluded from clustering because they had no valid
              pickup/dropoff coordinates
        """
        if not deliveries:
            logger.warning("No deliveries provided for clustering")
            return {}, []

        # Calculate centroid for each delivery that has valid coordinates. Deliveries
        # without valid coordinates are excluded from clustering entirely rather than
        # approximated to (0.0, 0.0), which would otherwise create an artificial
        # cluster around the geographic origin and waste a driver's route time.
        delivery_centroids = []
        clusterable_deliveries = []
        deliveries_without_coordinates = []
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
                clusterable_deliveries.append(delivery)
            else:
                logger.warning(
                    f"Delivery {delivery.get('id')} excluded from clustering: "
                    "missing pickup or dropoff coordinates"
                )
                deliveries_without_coordinates.append(delivery)

        if not delivery_centroids:
            logger.warning("No deliveries with valid coordinates to cluster")
            return {}, deliveries_without_coordinates

        # Perform clustering
        labels = self.clusterer.fit_predict(delivery_centroids)

        # Group deliveries by region
        regions: dict[int, list[dict[str, Any]]] = {}
        for delivery, label in zip(clusterable_deliveries, labels):
            if label not in regions:
                regions[label] = []
            regions[label].append(delivery)

        self._persist_region_geometry(delivery_centroids, labels)

        logger.info(
            f"Clustered {len(clusterable_deliveries)} deliveries into {len(regions)} regions "
            f"({len(deliveries_without_coordinates)} excluded for missing coordinates)"
        )
        return regions, deliveries_without_coordinates

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
