from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_current_user
from app.schemas.driver import AssignVehicleRequest, DriverResponse
from app.services.driver_service import assign_vehicle_to_driver

router = APIRouter(prefix="/api/v1/drivers", tags=["drivers"])


@router.post("/{driver_id}/assign_vehicle", response_model=DriverResponse, status_code=status.HTTP_200_OK)
async def assign_vehicle_to_driver_route(
    driver_id: str,
    payload: AssignVehicleRequest,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await assign_vehicle_to_driver(db, driver_id, payload)
