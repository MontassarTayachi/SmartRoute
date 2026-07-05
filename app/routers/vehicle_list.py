from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, status
from fastapi.responses import JSONResponse

from app.dependencies import get_current_user
from app.schemas.vehicle_list import VehicleListCreate, VehicleListResponse, VehicleListUpdate
from app.services.vehicle_list_service import (
    create_vehicle_list,
    delete_vehicle_list,
    get_vehicle_list_by_id,
    list_vehicle_list,
    update_vehicle_list,
)

router = APIRouter(prefix="/api/v1/vehicle-list", tags=["vehicle-list"])


@router.get("/", response_model=dict)
async def get_vehicle_list(
    page: int = 1,
    size: int = 10,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await list_vehicle_list(db, page=page, size=size)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_vehicle_list_route(
    nom: str = Form(...),
    image: UploadFile = File(None),
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    payload = VehicleListCreate(nom=nom)
    return await create_vehicle_list(db, payload, image_file=image)


@router.get("/{item_id}", response_model=VehicleListResponse)
async def get_vehicle_list_item(
    item_id: str,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    item = await get_vehicle_list_by_id(db, item_id)
    if not item:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Élément introuvable."},
        )
    return item


@router.put("/{item_id}", response_model=VehicleListResponse)
async def update_vehicle_list_route(
    item_id: str,
    nom: str = Form(None),
    image: UploadFile = File(None),
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    payload = VehicleListUpdate(nom=nom)
    return await update_vehicle_list(db, item_id, payload, image_file=image)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle_list_route(
    item_id: str,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    await delete_vehicle_list(db, item_id)
