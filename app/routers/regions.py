from flask import Blueprint, current_app, jsonify

from app.dependencies import require_auth
from app.services.optimization_settings_service import OptimizationSettingsService

regions_bp = Blueprint("regions", __name__, url_prefix="/api/regions")


@regions_bp.route("/geometry", methods=["GET"])
@require_auth
def get_regions_geometry():
    service = OptimizationSettingsService(current_app.mongodb)
    geometries = service.list_region_geometry()

    features = []
    for geometry in geometries:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [geometry.get("center_lng"), geometry.get("center_lat")],
                },
                "properties": {
                    "region_id": geometry.get("region_id"),
                    "radius_km": geometry.get("radius_km"),
                    "computed_at": geometry.get("computed_at"),
                },
            }
        )

    return jsonify({"type": "FeatureCollection", "features": features}), 200