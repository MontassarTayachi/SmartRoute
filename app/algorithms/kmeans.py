import logging
from typing import Any

import numpy as np
from sklearn.cluster import KMeans


logger = logging.getLogger(__name__)


class KMeansClusterer:
    """K-Means clustering algorithm for geographic delivery clustering."""

    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        """
        Initialize K-Means clusterer.

        Args:
            n_clusters: Number of clusters (regions)
            random_state: Random seed for reproducibility
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)

    def fit_predict(self, coordinates: list[tuple[float, float]]) -> list[int]:
        """
        Fit K-Means and predict cluster labels.

        Args:
            coordinates: List of (latitude, longitude) tuples

        Returns:
            List of cluster labels for each coordinate
        """
        if not coordinates:
            logger.warning("No coordinates provided for clustering")
            return []

        if len(coordinates) < self.n_clusters:
            logger.warning(
                f"Number of coordinates ({len(coordinates)}) is less than "
                f"number of clusters ({self.n_clusters}). Using {len(coordinates)} clusters."
            )
            self.n_clusters = max(1, len(coordinates))
            self.kmeans = KMeans(
                n_clusters=self.n_clusters, random_state=self.random_state, n_init=10
            )

        X = np.array(coordinates)
        labels = self.kmeans.fit_predict(X)
        return labels.tolist()

    def get_cluster_centers(self) -> list[tuple[float, float]]:
        """
        Get the center coordinates of each cluster.

        Returns:
            List of (latitude, longitude) tuples for cluster centers
        """
        centers = self.kmeans.cluster_centers_
        return [(center[0], center[1]) for center in centers]

    def assign_to_nearest_cluster(
        self, coordinates: list[tuple[float, float]]
    ) -> list[int]:
        """
        Assign new coordinates to the nearest existing cluster.

        Args:
            coordinates: List of (latitude, longitude) tuples

        Returns:
            List of cluster labels for each coordinate
        """
        if not coordinates:
            return []

        X = np.array(coordinates)
        labels = self.kmeans.predict(X)
        return labels.tolist()

    def calculate_centroid(
        self, coordinates: list[tuple[float, float]]
    ) -> tuple[float, float]:
        """
        Calculate the centroid (average position) of a set of coordinates.

        Args:
            coordinates: List of (latitude, longitude) tuples

        Returns:
            Tuple of (latitude, longitude) for the centroid
        """
        if not coordinates:
            return (0.0, 0.0)

        lats = [coord[0] for coord in coordinates]
        lngs = [coord[1] for coord in coordinates]
        return (sum(lats) / len(lats), sum(lngs) / len(lngs))
