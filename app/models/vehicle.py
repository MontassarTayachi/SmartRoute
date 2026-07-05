from datetime import datetime
from enum import Enum


class VehicleStatus(str, Enum):
    available = "available"
    in_use = "in_use"
    maintenance = "maintenance"
    out_of_service = "out_of_service"


class Vehicle:
    def __init__(
        self,
        registration: str,
        vehicle_list_id: str,
        capacity_kg: int,
        status: VehicleStatus,
        avg_fuel_consumption: float,
        created_at: datetime | None = None,
    ):
        self.registration = registration
        self.vehicle_list_id = vehicle_list_id
        self.capacity_kg = capacity_kg
        self.status = status
        self.avg_fuel_consumption = avg_fuel_consumption
        self.created_at = created_at
