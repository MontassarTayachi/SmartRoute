from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    vehicle_id: str = Field(..., example="507f1f77bcf86cd799439011")
    lat: float = Field(..., ge=-90, le=90, example=48.8566)
    lng: float = Field(..., ge=-180, le=180, example=2.3522)
    speed_kmh: float = Field(..., ge=0, example=42.3)
    heading: float = Field(..., ge=0, le=360, example=90)
    timestamp: datetime = Field(..., example="2026-07-08T10:30:00Z")


class LocationResponse(LocationCreate):
    id: str = Field(..., alias="_id")

    model_config = {
        "populate_by_name": True,
    }


class LiveVehicleLocationResponse(BaseModel):
    vehicle_id: str
    lat: float
    lng: float
    speed_kmh: float
    timestamp: datetime
