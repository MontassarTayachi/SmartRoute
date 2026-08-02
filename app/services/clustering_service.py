import logging
from typing import Any

from app.algorithms.kmeans import KMeansClusterer


logger = logging.getLogger(__name__)


class ClusteringService:
    """Service for geographic clustering of deliveries."""

    def __init__(self, n_clusters: int = 5):
        """
        Initialize clustering service.

        Args:
            n_clusters: Number of clusters (regions) to create
        """
        self.n_clusters = n_clusters
        self.clusterer = KMeansClusterer(n_clusters=n_clusters)

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

            if pickup_lat and pickup_lng and dropoff_lat and dropoff_lng:
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

        if pickup_lat and pickup_lng and dropoff_lat and dropoff_lng:
            centroid_lat = (pickup_lat + dropoff_lat) / 2
            centroid_lng = (pickup_lng + dropoff_lng) / 2
            centroid = (centroid_lat, centroid_lng)

            labels = self.clusterer.assign_to_nearest_cluster([centroid])
            return labels[0] if labels else 0

        return 0
