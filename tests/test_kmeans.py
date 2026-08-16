import pytest
from app.algorithms.kmeans import KMeansClusterer


def test_kmeans_basic_clustering():
    """Test basic K-Means clustering functionality."""
    clusterer = KMeansClusterer(n_clusters=3, random_state=42)

    coordinates = [
        (48.8566, 2.3522),  # Paris
        (48.8666, 2.3722),  # Near Paris
        (51.5074, -0.1278),  # London
        (51.5174, -0.1478),  # Near London
        (40.7128, -74.0060),  # New York
        (40.7228, -74.0260),  # Near New York
    ]

    labels = clusterer.fit_predict(coordinates)

    assert len(labels) == 6
    assert all(isinstance(label, int) for label in labels)
    assert max(labels) <= 2


def test_kmeans_empty_coordinates():
    """Test K-Means with empty coordinates."""
    clusterer = KMeansClusterer(n_clusters=3)
    labels = clusterer.fit_predict([])
    assert labels == []


def test_kmeans_single_coordinate():
    """Test K-Means with single coordinate."""
    clusterer = KMeansClusterer(n_clusters=3)
    labels = clusterer.fit_predict([(48.8566, 2.3522)])
    assert len(labels) == 1


def test_kmeans_centroid_calculation():
    """Test centroid calculation."""
    clusterer = KMeansClusterer()

    coordinates = [
        (48.0, 2.0),
        (50.0, 4.0),
    ]

    centroid = clusterer.calculate_centroid(coordinates)
    assert centroid == (49.0, 3.0)


def test_kmeans_cluster_centers():
    """Test getting cluster centers."""
    clusterer = KMeansClusterer(n_clusters=2, random_state=42)

    coordinates = [
        (48.8566, 2.3522),
        (48.8666, 2.3722),
        (51.5074, -0.1278),
        (51.5174, -0.1478),
    ]

    clusterer.fit_predict(coordinates)
    centers = clusterer.get_cluster_centers()

    assert len(centers) == 2
    assert all(len(center) == 2 for center in centers)


def test_kmeans_n_clusters_reduction_does_not_persist_across_calls():
    """A small batch must not permanently shrink n_clusters for a later, larger batch."""
    clusterer = KMeansClusterer(n_clusters=5, random_state=42)

    small_batch = [(48.8566, 2.3522), (48.8666, 2.3722)]
    labels = clusterer.fit_predict(small_batch)
    assert len(labels) == 2
    assert clusterer.n_clusters == 5
    assert clusterer.last_effective_n_clusters == 2

    large_batch = [
        (48.8566, 2.3522),
        (48.8666, 2.3722),
        (51.5074, -0.1278),
        (51.5174, -0.1478),
        (40.7128, -74.0060),
        (40.7228, -74.0260),
        (35.6895, 139.6917),
        (35.6995, 139.7017),
        (-33.8688, 151.2093),
        (-33.8788, 151.2193),
    ]
    labels = clusterer.fit_predict(large_batch)

    assert clusterer.n_clusters == 5
    assert clusterer.last_effective_n_clusters == 5
    assert len(set(labels)) == 5


def test_kmeans_assign_to_nearest_cluster():
    """Test assigning new coordinates to nearest cluster."""
    clusterer = KMeansClusterer(n_clusters=2, random_state=42)

    coordinates = [
        (48.8566, 2.3522),
        (48.8666, 2.3722),
        (51.5074, -0.1278),
        (51.5174, -0.1478),
    ]

    clusterer.fit_predict(coordinates)

    new_coordinates = [(48.8766, 2.3822)]
    labels = clusterer.assign_to_nearest_cluster(new_coordinates)

    assert len(labels) == 1
    assert labels[0] in [0, 1]
