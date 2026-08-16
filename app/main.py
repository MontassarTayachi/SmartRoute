import json
import logging
from datetime import datetime
from pathlib import Path

from bson import ObjectId
from flask import Flask, jsonify, send_from_directory
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

from app.core.config import settings
from app.core.exceptions import APIException
from app.db.init_db import initialize_database
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.socket_manager import socketio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class SmartRouteJSONProvider(DefaultJSONProvider):
    """Custom JSON provider that handles datetime and ObjectId serialization."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    app.url_map.strict_slashes = False
    app.json_provider_class = SmartRouteJSONProvider
    app.json = SmartRouteJSONProvider(app)

    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Database
    client, db = connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    app.mongodb_client = client
    app.mongodb = db

    initialize_database(settings.MONGO_URI, settings.MONGO_DB)

    # Uploads directory — use absolute path so send_from_directory works regardless of CWD
    uploads_abs = Path(__file__).parent.parent / "uploads"
    uploads_abs.mkdir(exist_ok=True)

    @app.route("/uploads/<path:filename>")
    def serve_uploads(filename):
        return send_from_directory(str(uploads_abs), filename)

    # Error handlers
    @app.errorhandler(APIException)
    def handle_api_exception(e):
        return jsonify({"detail": e.detail}), e.status_code

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"detail": "Resource introuvable."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"detail": "Méthode non autorisée."}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"detail": "Erreur interne du serveur."}), 500

    # Register blueprints — order matters: /live and /locations must come before /<vehicle_id>
    from app.routers.auth import auth_bp
    from app.routers.users import users_bp
    from app.routers.locations import locations_bp
    from app.routers.routes import routes_bp
    from app.routers.driver_assignments import driver_assignments_bp
    from app.routers.admin_optimization import admin_optimization_bp
    from app.routers.regions import regions_bp
    from app.routers.vehicles_live import vehicles_live_bp
    from app.routers.tracking import tracking_bp
    from app.routers.vehicles import vehicles_bp
    from app.routers.drivers import drivers_bp
    from app.routers.vehicle_list import vehicle_list_bp
    from app.routers.missions import missions_bp
    from app.routers.deliveries import deliveries_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(driver_assignments_bp)
    app.register_blueprint(admin_optimization_bp)
    app.register_blueprint(regions_bp)
    app.register_blueprint(vehicles_live_bp)
    app.register_blueprint(tracking_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(drivers_bp)
    app.register_blueprint(vehicle_list_bp)
    app.register_blueprint(missions_bp)
    app.register_blueprint(deliveries_bp)

    return app


def create_app_with_scheduler() -> Flask:
    app = create_app()

    socketio.init_app(app, cors_allowed_origins="*", async_mode="gevent")

    # Register SocketIO tracking events
    from app.routers.tracking import register_tracking_socket
    register_tracking_socket(socketio)

    # Scheduler
    from app.services.scheduler_service import SchedulerService
    from app.services.mission_service import MissionService

    scheduler_service = SchedulerService()

    def daily_mission_generation():
        with app.app_context():
            try:
                MissionService(app.mongodb).generate_missions_for_date(datetime.utcnow())
            except Exception as exc:
                logging.getLogger(__name__).error(f"Error in daily mission generation: {exc}")

    scheduler_service.add_daily_mission_generation(daily_mission_generation, hour=5, minute=55)
    scheduler_service.start()
    app.scheduler_service = scheduler_service

    return app


if __name__ == "__main__":
    from gevent import monkey
    monkey.patch_all()

    app = create_app_with_scheduler()
    socketio.run(app, host="0.0.0.0", port=8000, debug=False)
