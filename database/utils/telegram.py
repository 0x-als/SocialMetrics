from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine


class TelegramRepo:
    def __init__(self):
        self.log_file = "TelegramRepo.log"

    async def create_session(self, phone, api_id, api_hash):
        logger = logger_config(name="create_session", log_file=self.log_file)

        try:

            enc_api_id = await security.encrypt(str(api_id))
            enc_api_hash = await security.encrypt(str(api_hash))

            async with get_session() as session:

                try:

                    account = ScrapeAccounts(
                        api_key=enc_api_id,
                        token_hash=enc_api_hash,
                        path=f"{phone}.session",
                        type="telegram",
                        status=True
                    )
                    session.add(account)
                    await session.commit()
                    return True

                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def save_network_items(self, data):
        logger = logger_config(name="save_network_items", log_file=self.log_file)
        if not data:
            return

        objects = []
        batch_size = 1000
        try:
            async with get_session() as session:
                try:
                    for item in data:
                        objects.append({
                            "_network_id": item["network_item_id"],
                            "url": item["url"],
                            "status": True,
                            "published_at": item.get("published_at")
                        })

                    for i in range(0, len(objects), batch_size):
                        batch = objects[i:i + batch_size]
                        stmt = (
                            insert(NetworkItems)
                            .values(batch)
                            .on_conflict_do_nothing(index_elements=["_network_id", "url"])
                        )
                        await session.execute(stmt)
                        await session.commit()
                        logger.info(f"Saved batch {i // batch_size + 1} ({len(batch)} items)")

                    logger.info(f"Total saved {len(objects)} telegram items")

                except Exception as ex:
                    logger.exception(ex)
                    await session.rollback()
        except Exception as ex:
            logger.exception(ex)
