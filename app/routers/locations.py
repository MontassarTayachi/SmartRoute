from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_current_user
from app.schemas.location import LocationCreate, LocationResponse
from app.services.location_service import create_location

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location_route(
    payload: LocationCreate,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await create_location(db, payload)
