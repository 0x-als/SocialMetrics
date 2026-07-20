from sqlalchemy.orm import selectinload

from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine


class UsersRepo:
    def __init__(self):
        self.log_file = "UsersRepo.log"

    async def get_all_users(self):
        logger = logger_config(name="get_all_users", log_file=self.log_file)
        try:
            async with get_session() as session:
                try:
                    query = (
                        select(Users)
                        .options(selectinload(Users.role))
                        .order_by(Users.login)
                    )
                    result = await session.execute(query)
                    return result.scalars().all()
                except Exception as ex:
                    logger.exception(ex)
                    return []
        except Exception as ex:
            logger.exception(ex)
            return []

    async def get_user_by_id(self, user_id: int):
        logger = logger_config(name="get_user_by_id", log_file=self.log_file)
        try:
            async with get_session() as session:
                try:
                    result = await session.execute(
                        select(Users)
                        .options(
                            selectinload(Users.role)
                        )
                        .where(
                            Users.id == user_id
                        )
                    )
                    return result.scalar_one_or_none()
                except Exception as ex:
                    logger.exception(ex)
                    return None
        except Exception as ex:
            logger.exception(ex)
            return None

    async def get_user_login(self, login):
        logger = logger_config(name="get_user_login", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(Users).where(Users.login == login)
                    result = await session.execute(query)
                    user = result.scalar_one_or_none()

                    if user:
                        return user

                    else:
                        return None

                except Exception as ex:
                    logger.exception(ex)

        except Exception as ex:
            logger.exception(ex)

    async def create_user(self, login: str, password_hash: str, role_id: int):
        logger = logger_config(name="create_user", log_file=self.log_file)
        try:
            async with get_session() as session:
                try:
                    user = Users(
                        login=login,
                        password_hash=password_hash,
                        _role_id=role_id
                    )
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                    return user
                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)
                    return None
        except Exception as ex:
            logger.exception(ex)
            return None

    async def delete_user(self, user_id: int):
        logger = logger_config(name="delete_user", log_file=self.log_file)
        try:
            async with get_session() as session:
                try:
                    result = await session.execute(
                        select(Users).where(
                            Users.id == user_id
                        )
                    )
                    user = result.scalar_one_or_none()
                    if not user:
                        return False
                    await session.delete(user)
                    await session.commit()
                    return True
                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)
                    return False
        except Exception as ex:
            logger.exception(ex)
            return False