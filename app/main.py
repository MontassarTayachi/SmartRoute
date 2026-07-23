from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.db.init_db import initialize_database
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.routers.auth import router as auth_router
from app.routers.deliveries import router as deliveries_router
from app.routers.driver_assignments import router as driver_assignments_router
from app.routers.users import router as users_router
from app.routers.vehicles_live import router as vehicles_live_router
from app.routers.tracking import router as tracking_router
from app.routers.vehicles import router as vehicles_router
from app.routers.drivers import router as drivers_router
from app.routers.locations import router as locations_router
from app.routers.vehicle_list import router as vehicle_list_router
from app.routers.routes import router as routes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan de l'application : initialisation MongoDB et création des collections."""
    app.state.mongo_client, app.state.mongodb = connect_to_mongo(
        settings.MONGO_URI, settings.MONGO_DB
    )
    initialize_database(settings.MONGO_URI, settings.MONGO_DB)
    yield
    await close_mongo_connection(app.state.mongo_client)


app = FastAPI(
    title="SmartRoute API",
    version="0.1.0",
    description="API FastAPI pour la gestion de flotte SmartRoute.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Créer le dossier uploads s'il n'existe pas
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Monter le dossier des fichiers statiques (uploads)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(deliveries_router)
app.include_router(locations_router)
app.include_router(routes_router)
app.include_router(driver_assignments_router)
app.include_router(vehicles_live_router)
app.include_router(tracking_router)
app.include_router(vehicles_router)
app.include_router(drivers_router)
app.include_router(vehicle_list_router)
