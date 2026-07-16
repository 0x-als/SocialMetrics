from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine


class YoutubeRepo:
    def __init__(self):
        self.log_file = "YoutubeRepo.log"

    async def create_session(self, api_key):
        logger = logger_config(name="create_session", log_file=self.log_file)

        try:

            enc_api_key = await security.encrypt(api_key)

            async with get_session() as session:
                try:

                    account = ScrapeAccounts(
                        api_key=enc_api_key,
                        type="youtube"
                    )
                    session.add(account)
                    await session.commit()
                    return True


                except Exception as ex:
                    logger.exception(ex)
                    return False

        except ExceptionGroup as ex:
            logger.exception(ex)
            return False

    async def save_network_items(self, data):
        logger = logger_config(name="save_network_items", log_file=self.log_file)

        objects = []
        try:

            async with get_session() as session:
                try:

                    for item in data:
                        row = item[0]
                        network_id = row["id"]
                        urls = row["urls"]

                        for url in urls:
                            objects.append({
                                "_network_id": network_id,
                                "url": url,
                                "status": True
                            })

                    if objects:
                        stmt = (
                            insert(NetworkItems)
                            .values(objects)
                            .on_conflict_do_nothing(
                                index_elements=["_network_id", "url"]
                            )
                        )
                        await session.execute(stmt)
                        await session.commit()

                        logger.info(f"Saved {len(objects)} network items (duplicates skipped)")

                except Exception as ex:
                    logger.exception(ex)

        except Exception as ex:
            logger.exception(ex)
