from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VehicleLocationWrite(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, example=48.8566)
    longitude: float = Field(..., ge=-180, le=180, example=2.3522)
    timestamp: datetime = Field(..., example="2026-07-09T11:00:00Z")


class VehicleLocation(BaseModel):
    vehicle_id: str = Field(..., example="507f1f77bcf86cd799439011")
    vehicle_name: str | None = Field(None, example="Renault Master AB-123-CD")
    driver_name: str | None = Field(None, example="Jean Dupont")
    latitude: float = Field(..., ge=-90, le=90, example=48.8566)
    longitude: float = Field(..., ge=-180, le=180, example=2.3522)
    timestamp: datetime = Field(..., example="2026-07-09T11:00:00Z")


class VehicleLocationHistoryResponse(BaseModel):
    items: list[VehicleLocation]
    total: int
    page: int
    limit: int
