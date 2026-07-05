from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.dependencies import get_current_user
from app.schemas.driver import DriverCreate, DriverResponse, DriverUpdate
from app.services.driver_service import create_driver, list_drivers, list_drivers_without_user_account, update_driver

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
