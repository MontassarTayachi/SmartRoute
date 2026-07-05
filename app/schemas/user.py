from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    admin = "admin"
    dispatcher = "dispatcher"
    driver = "driver"
    viewer = "viewer"


class UserBase(BaseModel):
    name: str = Field(..., example="Alice Martin")
    email: EmailStr = Field(..., example="alice@example.com")
    role: UserRole = Field(..., example=UserRole.dispatcher)
    is_active: bool = Field(default=True, example=True)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="StrongP@ssw0rd")


class DriverUserCreate(BaseModel):
    driver_id: str = Field(..., example="650a1c2f4e0f826f4a2d3b1d")
    name: str = Field(..., example="Jean Dupont")
    email: EmailStr = Field(..., example="jean.dupont@example.com")
    password: str = Field(..., min_length=8, example="StrongP@ssw0rd")
    is_active: bool = Field(default=True, example=True)


class UserUpdate(BaseModel):
    name: str | None = Field(None, example="Alice Martin")
    email: EmailStr | None = Field(None, example="alice@example.com")
    role: UserRole | None = Field(None, example=UserRole.dispatcher)
    is_active: bool | None = Field(None, example=True)
    password: str | None = Field(None, min_length=8, example="NewP@ssword123")


class UserResponse(UserBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
    }


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = Field(default="bearer")
    user: UserResponse
