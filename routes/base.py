import asyncio
import json
from typing import Annotated
from enum import StrEnum

from fastapi import Depends, APIRouter, Body, WebSocket, Query, HTTPException
from mqtt import mqtt

from users import current_active_user, UserManager, get_user_manager, JWTStrategy, get_jwt_strategy
from connection_manager import ConnectionManager
from misc import logger
from misc.data import DataLoader

manager = ConnectionManager()

router = APIRouter(dependencies=[Depends(current_active_user)])


async def on_reload():
    mqtt.publish('api/data-refresh', qos=1)
    await manager.broadcast(json.dumps({
        'target': 'app',
        'data': {
            'event': {'type': 'refresh'}
        }
    }))


def create_dataloader():
    global data_loader
    logger.debug('Creating DataLoader instance')
    loop = asyncio.get_event_loop()
    data_loader = DataLoader(loop, on_reload=on_reload,
                             on_error=create_dataloader)
    data_loader.start()


create_dataloader()


async def data_refresh():
    data_loader.reload()


@router.get('/')
async def get():
    return {
        'devices': await get_devices(),
        'tags': await get_tags(),
        'locations': await get_locations(),
    }


@router.get('/devices')
async def get_devices() -> list:
    async with data_loader:
        return data_loader.devices


@router.get('/tags')
async def get_tags() -> list:
    async with data_loader:
        return data_loader.tags


@router.get('/locations')
async def get_locations() -> list:
    async with data_loader:
        return data_loader.locations


class MethodTarget(StrEnum):
    device = 'device'
    tag = 'tag'
    location = 'location'


@router.post('/{target}/{method_name}')
async def method(target: MethodTarget, method_name, params: Annotated[dict, Body()]):
    logger.debug('Method %s %s', target, method_name)
    mqtt.publish(f'api/{str(target)}/{method_name}',
                 json.dumps(params),
                 qos=1)


@router.websocket('/ws')
async def ws(websocket: WebSocket, token: str = Query(...),
             jwt_strategy: JWTStrategy = Depends(get_jwt_strategy),
             user_manager: UserManager = Depends(get_user_manager)):
    async with data_loader:
        await manager.connect(websocket)
        try:
            user = await jwt_strategy.read_token(token, user_manager)
            if user is None:
                raise HTTPException(401)
        except:
            await websocket.send_json({'error': {'message': 'Authentication failed'}})
            await websocket.close(code=1000)
            return
        while True:
            try:
                message = await websocket.receive_json()
                if message['command'] == 'fetch':
                    mqtt.publish(
                        f'api/{message["target"]}/fetch', json.dumps(message))
            except:
                manager.disconnect(websocket)
                break
