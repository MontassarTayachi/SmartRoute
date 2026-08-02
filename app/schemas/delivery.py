from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DeliveryStatus(str, Enum):
    pending = "pending"
    assigned = "assigned"
    picked = "picked"
    in_progress = "in_progress"
    delivered = "delivered"
    cancelled = "cancelled"


class DeliveryBase(BaseModel):
    customer: str = Field(..., min_length=1, example="ACME Corp")
    pickup_address: str = Field(..., min_length=1, example="10 Rue de Rivoli, Paris")
    pickup_address_lat: float = Field(..., ge=-90, le=90, example=48.8566)
    pickup_address_lng: float = Field(..., ge=-180, le=180, example=2.3522)
    dropoff_address: str = Field(..., min_length=1, example="25 Avenue des Champs-Élysées, Paris")
    dropoff_address_lat: float = Field(..., ge=-90, le=90, example=48.8666)
    dropoff_address_lng: float = Field(..., ge=-180, le=180, example=2.3722)
    weight_kg: float = Field(..., ge=0, example=125.5)
    priority: str = Field(..., min_length=1, example="high")
    scheduled_at: datetime = Field(..., example="2026-07-08T10:30:00Z")


class DeliveryCreate(DeliveryBase):
    pass


class DeliveryUpdate(BaseModel):
    customer: str | None = Field(None, min_length=1, example="ACME Corp")
    pickup_address: str | None = Field(None, min_length=1, example="10 Rue de Rivoli, Paris")
    pickup_address_lat: float | None = Field(None, ge=-90, le=90, example=48.8566)
    pickup_address_lng: float | None = Field(None, ge=-180, le=180, example=2.3522)
    dropoff_address: str | None = Field(None, min_length=1, example="25 Avenue des Champs-Élysées, Paris")
    dropoff_address_lat: float | None = Field(None, ge=-90, le=90, example=48.8666)
    dropoff_address_lng: float | None = Field(None, ge=-180, le=180, example=2.3722)
    weight_kg: float | None = Field(None, ge=0, example=125.5)
    priority: str | None = Field(None, min_length=1, example="high")
    scheduled_at: datetime | None = Field(None, example="2026-07-08T10:30:00Z")
    vehicle_id: str | None = Field(None, example="507f1f77bcf86cd799439011")
    driver_id: str | None = Field(None, example="507f191e810c19729de860ea")


class DeliveryAssignRequest(BaseModel):
    vehicle_id: str = Field(..., example="507f1f77bcf86cd799439011")
    driver_id: str = Field(..., example="507f191e810c19729de860ea")


class DeliveryStatusUpdateRequest(BaseModel):
    status: DeliveryStatus = Field(..., example=DeliveryStatus.in_progress)


class DeliveryResponse(BaseModel):
    id: str = Field(..., alias="_id")
    reference: str
    customer: str
    pickup_address: str | None = None
    pickup_address_lat: float | None = None
    pickup_address_lng: float | None = None
    dropoff_address: str | None = None
    dropoff_address_lat: float | None = None
    dropoff_address_lng: float | None = None
    weight_kg: float
    priority: str
    scheduled_at: datetime
    status: DeliveryStatus
    vehicle_id: str | None = None
    driver_id: str | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    vehicle: dict[str, Any] | None = None
    driver: dict[str, Any] | None = None

    model_config = {
        "populate_by_name": True,
    }


class DeliveryListResponse(BaseModel):
    items: list[DeliveryResponse]
    total: int
    page: int
    limit: int
