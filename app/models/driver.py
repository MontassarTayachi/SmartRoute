from enum import Enum


class Availability(str, Enum):
    available = "available"
    unavailable = "unavailable"


class Driver:
    def __init__(
        self,
        full_name: str,
        phone: str,
        license_number: str,
        availability: Availability,
        assigned_vehicle_id: str | None = None,
        login_user_id: str | None = None,
    ):
        self.full_name = full_name
        self.phone = phone
        self.license_number = license_number
        self.availability = availability
        self.assigned_vehicle_id = assigned_vehicle_id
        self.login_user_id = login_user_id
