from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.dependencies import get_current_user
from app.schemas.vehicle import VehicleCreate, VehicleResponse, VehicleUpdate
from app.services.vehicle_service import (
    create_vehicle,
    delete_vehicle,
    get_vehicle_by_id,
    list_unassigned_vehicles,
    list_vehicles,
    update_vehicle,
)

router = APIRouter(prefix="/api/v1/vehicles", tags=["vehicles"])


@router.get("/", response_model=dict)
async def get_vehicles(
    status: str | None = None,
    vehicle_list_id: str | None = None,
    page: int = 1,
    size: int = 10,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await list_vehicles(db, page=page, size=size, status=status, vehicle_list_id=vehicle_list_id)


@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle_route(payload: VehicleCreate, request: Request = None, current_user: dict = Depends(get_current_user)):
    db = request.app.state.mongodb
    return await create_vehicle(db, payload)


@router.get("/dispo", response_model=dict)
async def get_available_vehicles(
    page: int = 1,
    size: int = 10,
    request: Request = None,
):
    db = request.app.state.mongodb
    return await list_unassigned_vehicles(db, page=page, size=size)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle_route(vehicle_id: str, request: Request = None, current_user: dict = Depends(get_current_user)):
    db = request.app.state.mongodb
    vehicle = await get_vehicle_by_id(db, vehicle_id)
    if not vehicle:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Véhicule introuvable."})
    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle_route(vehicle_id: str, payload: VehicleUpdate, request: Request = None, current_user: dict = Depends(get_current_user)):
    db = request.app.state.mongodb
    return await update_vehicle(db, vehicle_id, payload)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle_route(vehicle_id: str, request: Request = None, current_user: dict = Depends(get_current_user)):
    db = request.app.state.mongodb
    await delete_vehicle(db, vehicle_id)
