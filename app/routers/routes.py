from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, status

from app.dependencies import get_current_user
from app.schemas.route import RouteHistoryItem, RouteOptimizeRequest, RouteOptimizeResponse
from app.services.route_service import get_route_history, optimize_route

router = APIRouter(prefix="/api/v1/routes", tags=["routes"])


@router.get("/history", response_model=list[RouteHistoryItem], status_code=status.HTTP_200_OK)
async def get_routes_history_route(
    vehicle_id: str | None = None,
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await get_route_history(db, vehicle_id=vehicle_id, from_dt=from_date, to_dt=to_date)


@router.post("/optimiz", response_model=RouteOptimizeResponse, status_code=status.HTTP_200_OK)
async def optimize_route_route(
    payload: RouteOptimizeRequest,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await optimize_route(db, delivery_ids=payload.delivery_ids, constraints=payload.constraints)
