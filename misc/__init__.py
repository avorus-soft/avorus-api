import logging

from db import get_user_db_context
from users import get_user_manager_context, get_jwt_strategy

logger = logging.getLogger()
logging.basicConfig(level=logging.ERROR)


async def authenticate_token(token: str):
    jwt_strategy = get_jwt_strategy()
    async with get_user_db_context() as user_db:
        async with get_user_manager_context(user_db) as user_manager:
            return await jwt_strategy.read_token(token, user_manager=user_manager)
