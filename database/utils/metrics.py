import inspect
from config import *
from utils import security
from datetime import date
from sqlalchemy import *
from sqlalchemy.orm import *
from database.models import *
from utils.logger import logger_config
from sqlalchemy.orm import selectinload
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.dialects.postgresql import insert


class MetricsRepo:
    def __init__(self):
        self.log_file = "MetricsRepo.log"

    async def get_circle_last_metrics(self):
        logger = logger_config(
            name="get_circle_last_metrics",
            log_file=self.log_file
        )

        try:
            async with get_session() as session:

                im = aliased(ItemMetadata)

                latest_metadata = (
                    select(
                        ItemMetadata._item_id,
                        func.max(ItemMetadata.created_at).label("max_created_at")
                    )
                    .group_by(ItemMetadata._item_id)
                    .subquery()
                )

                query = (
                    select(
                        SocialNetworks.type.label("platform"),

                        func.sum(im.likes).label("likes"),
                        func.sum(im.views_video).label("views_video"),

                        func.sum(
                            case(
                                (
                                    func.length(func.coalesce(im.description, "")) > 0,
                                    1
                                ),
                                else_=0
                            )
                        ).label("description_count"),

                        func.sum(im.saves).label("saves"),
                        func.sum(im.reposts).label("reposts"),
                        func.sum(im.comments_count).label("comments_count")
                    )
                    .select_from(SocialNetworks)
                    .join(
                        NetworkItems,
                        NetworkItems._network_id == SocialNetworks.id
                    )
                    .join(
                        latest_metadata,
                        latest_metadata.c._item_id == NetworkItems.id
                    )
                    .join(
                        im,
                        and_(
                            im._item_id == NetworkItems.id,
                            im.created_at == latest_metadata.c.max_created_at
                        )
                    )
                    .group_by(SocialNetworks.type)
                )

                result = await session.execute(query)

                stats = []

                for row in result:
                    stats.append({
                        "platform": row.platform,

                        "likes": int(row.likes or 0),
                        "views_video": int(row.views_video or 0),
                        "description_count": int(row.description_count or 0),
                        "saves": int(row.saves or 0),
                        "reposts": int(row.reposts or 0),
                        "comments_count": int(row.comments_count or 0)
                    })

                return stats

        except Exception as ex:
            logger.exception(ex)
            return []

    async def get_line_metrics(self, user_id: int, type: str, metric: str, date_from: date, date_to: date):
        logger = logger_config(name="get_line_metrics", log_file=self.log_file)

        try:
            async with get_session() as session:

                im = aliased(ItemMetadata)
                metric_column = getattr(im, metric)

                latest_metadata = (
                    select(
                        ItemMetadata._item_id,
                        func.date(ItemMetadata.created_at).label("day"),
                        func.max(ItemMetadata.created_at).label("max_created_at")
                    )
                    .join(NetworkItems, NetworkItems.id == ItemMetadata._item_id)
                    .join(SocialNetworks, SocialNetworks.id == NetworkItems._network_id)
                    .where(
                        SocialNetworks._user_id == user_id,
                        SocialNetworks.type == type,
                        func.date(ItemMetadata.created_at) >= date_from,
                        func.date(ItemMetadata.created_at) <= date_to
                    )
                    .group_by(ItemMetadata._item_id, func.date(ItemMetadata.created_at))
                    .subquery()
                )

                query = (
                    select(
                        latest_metadata.c.day.label("day"),
                        func.sum(metric_column).label("value")
                    )
                    .select_from(latest_metadata)
                    .join(
                        im,
                        and_(
                            im._item_id == latest_metadata.c._item_id,
                            im.created_at == latest_metadata.c.max_created_at
                        )
                    )
                    .group_by(latest_metadata.c.day)
                    .order_by(latest_metadata.c.day)
                )

                result = await session.execute(query)

                points = [{"day": row.day.isoformat(), "value": int(row.value or 0)} for row in result]
                return {"points": points}

        except Exception as ex:
            logger.exception(ex)
            return {"points": []}
