from enum import StrEnum
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from . import PyObjectId


class ItemType(StrEnum):
    Device = 'device'
    Tag = 'tag'
    Location = 'location'


class EventActionsModel(BaseModel):
    start: str = Field()
    end: str = Field()


class ExtendedPropsModel(BaseModel):
    id: int = Field()
    type: ItemType = Field()
    label: str = Field()
    description: Optional[str] = Field()
    actions: EventActionsModel = Field()


class EventModel(BaseModel):
    id: PyObjectId = Field(alias='_id')
    title: str = Field()
    start: datetime = Field()
    end: Optional[datetime] = Field()
    allDay: bool = Field()
    rrule: Optional[str] = Field()
    duration: Optional[float] = Field()
    extendedProps: ExtendedPropsModel = Field()

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str,
                         datetime: lambda date: date.isoformat()}


class UpdateEventModel(BaseModel):
    title: Optional[str]
    start: Optional[datetime]
    end: Optional[datetime]
    allDay: Optional[bool]
    extendedProps: Optional[ExtendedPropsModel]
