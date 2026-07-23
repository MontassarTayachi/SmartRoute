from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.dependencies import get_current_user
from app.schemas.driver import AssignVehicleRequest, DriverCreate, DriverResponse, DriverUpdate, DriverCurrentResponse
from app.services.driver_service import (
    assign_vehicle_to_driver,
    create_driver,
    list_drivers,
    list_drivers_without_user_account,
    unassign_vehicle_from_driver,
    update_driver,
    get_driver_and_vehicle_with_current_user_context
)

router = APIRouter(prefix="/api/v1/drivers", tags=["drivers"])


@router.get("/", response_model=dict)
async def get_drivers(
    availability: str | None = None,
    page: int = 1,
    size: int = 10,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await list_drivers(db, page=page, size=size, availability=availability)


@router.get("/without-user-account", response_model=dict)
async def get_drivers_without_user_account(
    availability: str | None = None,
    page: int = 1,
    size: int = 10,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await list_drivers_without_user_account(db, page=page, size=size, availability=availability)


@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver_route(payload: DriverCreate, request: Request = None, current_user: dict = Depends(get_current_user)):
    db = request.app.state.mongodb
    return await create_driver(db, payload)


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver_route(driver_id: str, payload: DriverUpdate, request: Request = None, current_user: dict = Depends(get_current_user)):
    db = request.app.state.mongodb
    return await update_driver(db, driver_id, payload)


@router.post("/{driver_id}/assign-vehicle", response_model=DriverResponse)
async def assign_vehicle_route(
    driver_id: str,
    payload: AssignVehicleRequest,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await assign_vehicle_to_driver(db, driver_id, payload)


@router.post("/{driver_id}/unassign-vehicle", response_model=DriverResponse)
async def unassign_vehicle_route(
    driver_id: str,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await unassign_vehicle_from_driver(db, driver_id)


@router.get("/current", response_model=DriverCurrentResponse)
async def get_current_driver_route(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    driver, vehicle = await get_driver_and_vehicle_with_current_user_context(
        db,
        current_user["_id"],
    )

    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )
    return {
        "driver": driver,
        "vehicle": vehicle,
    }