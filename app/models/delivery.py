from datetime import datetime
from enum import Enum


class DeliveryStatus(str, Enum):
    pending = "pending"
    assigned = "assigned"
    picked = "picked"
    in_progress = "in_progress"
    delivered = "delivered"
    cancelled = "cancelled"


class Delivery:
    def __init__(
        self,
        reference: str,
        customer: str,
        pickup_address: str,
        pickup_address_lat: float,
        pickup_address_lng: float,
        dropoff_address: str,
        dropoff_address_lat: float,
        dropoff_address_lng: float,
        weight_kg: float,
        priority: str,
        scheduled_at: datetime,
        status: DeliveryStatus = DeliveryStatus.pending,
        vehicle_id: str | None = None,
        driver_id: str | None = None,
        delivered_at: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        id: str | None = None,
    ):
        self.id = id
        self.reference = reference
        self.customer = customer
        self.pickup_address = pickup_address
        self.pickup_address_lat = pickup_address_lat
        self.pickup_address_lng = pickup_address_lng
        self.dropoff_address = dropoff_address
        self.dropoff_address_lat = dropoff_address_lat
        self.dropoff_address_lng = dropoff_address_lng
        self.weight_kg = weight_kg
        self.priority = priority
        self.scheduled_at = scheduled_at
        self.status = status
        self.vehicle_id = vehicle_id
        self.driver_id = driver_id
        self.delivered_at = delivered_at
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
