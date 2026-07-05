from __future__ import annotations

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, object]) -> None:
        field_schema.update(type="string")


class BaseResponseModel(BaseModel):
    class Config:
        json_encoders = {
            ObjectId: str,
        }
