from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    driver = "driver"
    viewer = "viewer"


class User:
    def __init__(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: UserRole,
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
