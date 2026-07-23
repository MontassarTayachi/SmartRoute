from __future__ import annotations
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class VehicleStatus(str, Enum):
    available = "available"
    in_use = "in_use"
    maintenance = "maintenance"
    out_of_service = "out_of_service"


class VehicleBase(BaseModel):
    registration: str = Field(..., example="ABC-1234")
    vehicle_list_id: str = Field(..., example="507f1f77bcf86cd799439011")
    capacity_kg: int = Field(..., ge=0, example=1200)
    status: VehicleStatus = Field(default=VehicleStatus.available, example=VehicleStatus.available)
    avg_fuel_consumption: float = Field(..., ge=0, example=18.5)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    registration: str | None = Field(None, example="ABC-1234")
    vehicle_list_id: str | None = Field(None, example="507f1f77bcf86cd799439011")
    capacity_kg: int | None = Field(None, ge=0, example=1200)
    status: VehicleStatus | None = Field(None, example=VehicleStatus.maintenance)
    avg_fuel_consumption: float | None = Field(None, ge=0, example=19.1)


class VehicleResponse(VehicleBase):
    id: str = Field(..., alias="_id")
    created_at: datetime

    model_config = {
        "populate_by_name": True,
    }


class VehicleDispoResponse(VehicleResponse):
    nom: str | None = Field(None, example="Camion de livraison")
    image_url: str | None = Field(None, example="/uploads/vehicles/vehicle_1.jpg")
