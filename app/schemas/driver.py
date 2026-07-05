from __future__ import annotations
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Availability(str, Enum):
    available = "available"
    unavailable = "unavailable"


class DriverBase(BaseModel):
    full_name: str = Field(..., example="Jean Dupont")
    phone: str = Field(..., example="+33123456789")
    license_number: str = Field(..., example="PERM-123456")
    availability: Availability = Field(default=Availability.available, example=Availability.available)
    assigned_vehicle_id: str | None = Field(None, example="650a1c2f4e0f826f4a2d3b1c")
    login_user_id: str | None = Field(None, example="650a1c2f4e0f826f4a2d3b1d")


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    full_name: str | None = Field(None, example="Jean Dupont")
    phone: str | None = Field(None, example="+33123456789")
    license_number: str | None = Field(None, example="PERM-123456")
    availability: Availability | None = Field(None, example=Availability.available)
    assigned_vehicle_id: str | None = Field(None, example="650a1c2f4e0f826f4a2d3b1c")
    login_user_id: str | None = Field(None, example="650a1c2f4e0f826f4a2d3b1d")


class DriverResponse(DriverBase):
    id: str = Field(..., alias="_id")

    model_config = {
        "populate_by_name": True,
    }
