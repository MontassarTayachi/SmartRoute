from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel, Field


class VehicleListBase(BaseModel):
    nom: str = Field(..., min_length=1, example="Camion de livraison")
    image_url: str = Field(..., example="/uploads/vehicle_1.jpg")


class VehicleListCreate(BaseModel):
    nom: str = Field(..., min_length=1, example="Camion de livraison")


class VehicleListUpdate(BaseModel):
    nom: str | None = Field(None, min_length=1, example="Camion de livraison")


class VehicleListResponse(VehicleListBase):
    id: str = Field(..., alias="_id")
    created_at: datetime

    model_config = {
        "populate_by_name": True,
    }
