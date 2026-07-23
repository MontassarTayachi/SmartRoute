from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RouteHistoryItem(BaseModel):
    vehicle_id: str
    lat: float
    lng: float
    speed_kmh: float
    heading: float
    timestamp: datetime


class RouteOptimizeRequest(BaseModel):
    delivery_ids: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)


class RouteOptimizeResponse(BaseModel):
    route: list[dict[str, Any]]
    distance_km: float
    estimated_time: int
