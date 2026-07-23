from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_current_user
from app.schemas.location import LiveVehicleLocationResponse
from app.services.location_service import list_live_vehicle_locations

router = APIRouter(prefix="/api/v1/vehicles", tags=["vehicles"])


@router.get("/live", response_model=list[LiveVehicleLocationResponse], status_code=status.HTTP_200_OK)
async def list_live_vehicles_route(
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await list_live_vehicle_locations(db)
