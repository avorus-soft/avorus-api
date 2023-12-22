from datetime import datetime
from fastapi import Depends, APIRouter, Body, status
from fastapi.encoders import jsonable_encoder
from models.calendar import EventModel, UpdateEventModel
from users import current_active_user
from db import client
from mqtt import mqtt

db = client['calendar']

router = APIRouter(dependencies=[Depends(current_active_user)])


@router.get('/calendar/get_events')
async def get_events():
    events = []
    async for event in db['events'].find():
        events.append(jsonable_encoder(event))
    return events


@router.post('/calendar/save_event')
async def save_event(event: EventModel = Body()):
    payload = jsonable_encoder(event)
    if await db['events'].find_one({'_id': payload['_id']}) != None:
        await db['events'].update_one({'_id': str(payload['_id'])}, {"$set": payload})
        response = status.HTTP_200_OK
    else:
        await db['events'].insert_one(payload)
        response = status.HTTP_201_CREATED
    mqtt.publish('api/calendar/update', qos=1)
    return response


@router.delete('/calendar/delete_event/{id}')
async def delete_event(id: str):
    if await db['events'].find_one({'_id': id}) != None:
        await db['events'].delete_one({'_id': id})
        mqtt.publish('api/calendar/update', qos=1)
        return None
    else:
        return status.HTTP_404_NOT_FOUND
