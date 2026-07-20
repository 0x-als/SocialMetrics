from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine


class RolesRepo:
    def __init__(self):
        self.log_file = "RolerRepo.log"

    async def get_all_roles(self):
        logger = logger_config(name="get_all_roles", log_file=self.log_file)
        try:

            async with get_session() as session:
                try:

                    result = await session.execute(
                        select(Roles).order_by(Roles.title)
                    )
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)

        except Exception as ex:
            logger.exception(ex)

    async def get_role_by_id(self, role_id: int):
        logger = logger_config(name="get_role_by_id", log_file=self.log_file)
        try:
            async with get_session() as session:
                try:
                    result = await session.execute(
                        select(Roles).where(Roles.id == role_id)
                    )
                    return result.scalar_one_or_none()
                except Exception as ex:
                    logger.exception(ex)
                    return None
        except Exception as ex:
            logger.exception(ex)
            return None