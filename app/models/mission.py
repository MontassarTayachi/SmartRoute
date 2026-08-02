from datetime import datetime
from enum import Enum


class MissionStatus(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class MissionStep:
    def __init__(
        self,
        delivery_id: str,
        step_type: str,  # "pickup" or "delivery"
        address: str,
        lat: float,
        lng: float,
        order: int,
        is_done: bool = False,
    ):
        self.delivery_id = delivery_id
        self.step_type = step_type
        self.address = address
        self.lat = lat
        self.lng = lng
        self.order = order
        self.is_done = is_done


class Mission:
    def __init__(
        self,
        driver_id: str,
        vehicle_id: str,
        region_id: int,
        deliveries: list[str],
        deliveries_order: list[MissionStep],
        total_weight: float,
        route_distance: float,
        route_duration: int,
        status: MissionStatus = MissionStatus.planned,
        polyline: str | None = None,
        created_at: datetime | None = None,
        scheduled_date: datetime | None = None,
        updated_at: datetime | None = None,
        id: str | None = None,
    ):
        self.id = id
        self.driver_id = driver_id
        self.vehicle_id = vehicle_id
        self.region_id = region_id
        self.deliveries = deliveries
        self.deliveries_order = deliveries_order
        self.total_weight = total_weight
        self.route_distance = route_distance
        self.route_duration = route_duration
        self.status = status
        self.polyline = polyline
        self.created_at = created_at or datetime.utcnow()
        self.scheduled_date = scheduled_date or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
