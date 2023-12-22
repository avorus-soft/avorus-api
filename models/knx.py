from enum import StrEnum
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from . import PyObjectId


class KNXEventModel(BaseModel):
    id: PyObjectId = Field(alias='_id')
    target: int = Field()
    value: bool = Field()
    time: int = Field()

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
