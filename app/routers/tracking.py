from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.encoders import jsonable_encoder

from app.dependencies import get_current_user
from app.schemas.tracking import VehicleLocation, VehicleLocationHistoryResponse, VehicleLocationWrite
from app.services.tracking_service import (
    get_vehicle_latest_location,
    list_latest_vehicle_locations,
    list_vehicle_location_history,
    save_vehicle_location,
)


class VehicleTrackingConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        serialized_payload = jsonable_encoder(payload)
        active_connections = self._connections.copy()
        for websocket in active_connections:
            try:
                await websocket.send_json(serialized_payload)
            except Exception:
                self.disconnect(websocket)


tracking_manager = VehicleTrackingConnectionManager()

router = APIRouter(prefix="/api/v1", tags=["tracking"])


@router.post("/vehicles/{vehicle_id}/location", response_model=VehicleLocation, status_code=status.HTTP_200_OK)
async def post_vehicle_location_route(
    vehicle_id: str,
    payload: VehicleLocationWrite,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    location = await save_vehicle_location(db, vehicle_id=vehicle_id, payload=payload)
    await tracking_manager.broadcast(location)
    return location


@router.get("/vehicles/{vehicle_id}/location", response_model=VehicleLocation, status_code=status.HTTP_200_OK)
async def get_vehicle_location_route(
    vehicle_id: str,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await get_vehicle_latest_location(db, vehicle_id=vehicle_id)


@router.get("/vehicles/locations", response_model=list[VehicleLocation], status_code=status.HTTP_200_OK)
async def get_all_vehicle_locations_route(
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await list_latest_vehicle_locations(db)


@router.get(
    "/vehicles/{vehicle_id}/locations/history",
    response_model=VehicleLocationHistoryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_vehicle_location_history_route(
    vehicle_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.mongodb
    return await list_vehicle_location_history(db, vehicle_id=vehicle_id, page=page, limit=limit)


@router.websocket("/ws/vehicles/tracking")
async def vehicles_tracking_websocket(websocket: WebSocket):
    await tracking_manager.connect(websocket)

    try:
        db = websocket.app.state.mongodb
        latest_locations = await list_latest_vehicle_locations(db)
        for location in latest_locations:
            await websocket.send_json(jsonable_encoder(location))

        while True:
            # Keep the WebSocket alive; incoming payloads are ignored.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        tracking_manager.disconnect(websocket)
