from fastapi import APIRouter, Depends, Query, Request, status

from app.dependencies import get_current_user
from app.schemas.delivery import (
    DeliveryAssignRequest,
    DeliveryCreate,
    DeliveryListResponse,
    DeliveryResponse,
    DeliveryStatusUpdateRequest,
    DeliveryUpdate,
)
from app.services.delivery_service import (
    assign_delivery,
    create_delivery,
    get_delivery_by_id,
    list_deliveries,
    update_delivery,
    update_delivery_status,
)

router = APIRouter(prefix="/api/v1/deliveries", tags=["deliveries"])


@router.get("/", response_model=DeliveryListResponse, status_code=status.HTTP_200_OK)
async def list_deliveries_route(
    status_filter: str | None = Query(None, alias="status"),
    scheduled_at: str | None = Query(None, alias="scheduled_at"),
    date: str | None = None,
    page: int = 1,
    limit: int = 20,
    paginate: bool = True,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await list_deliveries(
        db,
        page=page,
        limit=limit,
        status_filter=status_filter,
        date_filter=scheduled_at or date,
        paginate=paginate,
    )


@router.post("/", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_route(
    payload: DeliveryCreate,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await create_delivery(db, payload)


@router.get("/{delivery_id}", response_model=DeliveryResponse, status_code=status.HTTP_200_OK)
async def get_delivery_route(
    delivery_id: str,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await get_delivery_by_id(db, delivery_id)


@router.put("/{delivery_id}", response_model=DeliveryResponse, status_code=status.HTTP_200_OK)
async def update_delivery_route(
    delivery_id: str,
    payload: DeliveryUpdate,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await update_delivery(db, delivery_id, payload)


@router.post("/{delivery_id}/assign", response_model=DeliveryResponse, status_code=status.HTTP_200_OK)
async def assign_delivery_route(
    delivery_id: str,
    payload: DeliveryAssignRequest,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await assign_delivery(
        db,
        delivery_id,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
    )


@router.post("/{delivery_id}/status", response_model=DeliveryResponse, status_code=status.HTTP_200_OK)
async def update_delivery_status_route(
    delivery_id: str,
    payload: DeliveryStatusUpdateRequest,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await update_delivery_status(db, delivery_id, payload.status.value)
