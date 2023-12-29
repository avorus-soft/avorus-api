from typing import Annotated
import yaml

from fastapi import Body, Depends, APIRouter

from users import current_active_admin
from connection_manager import ConnectionManager
from misc import logger
from .base import on_reload

manager = ConnectionManager()

router = APIRouter(dependencies=[Depends(current_active_admin)])


@router.get('/')
async def get():
    with open('/manager/config/config.yml') as f:
        return yaml.safe_load(f)


@router.post('/')
async def post_devicemap(body: Annotated[list, Body()]):
    with open('/manager/config/config.yml', 'w') as f:
        yaml.dump(body, f)
    await on_reload()
