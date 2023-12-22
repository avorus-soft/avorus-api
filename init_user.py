import os
import asyncio

import contextlib

from pydantic import EmailStr
from beanie import init_beanie

from db import db, User, get_user_db
from schemas import UserCreate
from users import get_user_manager
from fastapi_users.exceptions import UserAlreadyExists

get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(email: EmailStr, password: str, is_superuser: bool = False):
    try:
        await init_beanie(
            database=db,
            document_models=[
                User,
            ],
        )
        async with get_user_db_context() as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                user = await user_manager.create(
                    UserCreate(
                        email=email, password=password, is_superuser=is_superuser
                    )
                )
                print(f'User created {user}')
    except UserAlreadyExists:
        print(f'User {email} already exists')

if __name__ == '__main__':
    username = EmailStr(os.environ.get('API_SYSTEM_USERNAME'))
    password = str(os.environ.get('API_SYSTEM_PASSWORD'))
    asyncio.run(create_user(username, password, is_superuser=True))
