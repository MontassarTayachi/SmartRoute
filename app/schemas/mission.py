from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MissionStatus(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class MissionStepSchema(BaseModel):
    delivery_id: str = Field(..., example="507f1f77bcf86cd799439011")
    step_type: str = Field(..., example="pickup")
    address: str = Field(..., example="10 Rue de Rivoli, Paris")
    lat: float = Field(..., ge=-90, le=90, example=48.8566)
    lng: float = Field(..., ge=-180, le=180, example=2.3522)
    order: int = Field(..., ge=0, example=0)
    is_done: bool = Field(default=False, example=False)


class MissionBase(BaseModel):
    driver_id: str = Field(..., example="507f191e810c19729de860ea")
    vehicle_id: str = Field(..., example="507f1f77bcf86cd799439011")
    region_id: int = Field(..., ge=0, example=1)
    delivery_ids: list[str] = Field(..., example=["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"])
    deliveries_order: list[MissionStepSchema] = Field(...)
    total_weight: float = Field(..., ge=0, example=250.5)
    route_distance: float = Field(..., ge=0, example=15.5)
    route_duration: int = Field(..., ge=0, example=1800)


class MissionCreate(MissionBase):
    pass


class MissionUpdate(BaseModel):
    status: MissionStatus | None = Field(None, example=MissionStatus.in_progress)
    polyline: str | None = Field(None, example="encoded_polyline_string")


class MissionResponse(BaseModel):
    id: str = Field(..., alias="_id")
    driver_id: str
    vehicle_id: str
    region_id: int
    delivery_ids: list[str]
    deliveries_order: list[MissionStepSchema]
    total_weight: float
    route_distance: float
    route_duration: int
    status: MissionStatus
    polyline: str | None = None
    created_at: datetime
    driver: dict[str, Any] | None = None
    vehicle: dict[str, Any] | None = None

    model_config = {
        "populate_by_name": True,
    }


class MissionListResponse(BaseModel):
    items: list[MissionResponse]
    total: int
    page: int
    limit: int


class MissionGenerateRequest(BaseModel):
    date: datetime | None = Field(None, description="Date for mission generation (default: today)")


class DeliveryStepUpdateRequest(BaseModel):
    step_index: int = Field(..., ge=0, description="Index of the step in deliveries_order")
    is_done: bool = Field(..., description="New completion status of the step")
