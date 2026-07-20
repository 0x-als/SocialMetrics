import inspect

from config import *
from utils import security
from datetime import date, timedelta
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

    async def get_top_accounts(self):
        date_from = datetime.utcnow() - timedelta(days=7)
        async with get_session() as session:
            metadata_rank = (
                select(
                    ItemMetadata._item_id,
                    ItemMetadata.likes,
                    ItemMetadata.views_picture,
                    ItemMetadata.views_video,
                    ItemMetadata.saves,
                    ItemMetadata.reposts,
                    ItemMetadata.comments_count,
                    func.row_number().over(
                        partition_by=ItemMetadata._item_id,
                        order_by=ItemMetadata.created_at.desc()
                    ).label("rn")
                )
            ).subquery()
            result = await session.execute(
                select(
                    SocialNetworks.username,
                    SocialNetworks.type,
                    func.coalesce(
                        func.sum(metadata_rank.c.views_video),
                        0
                    ).label("views_video"),
                    func.coalesce(
                        func.sum(metadata_rank.c.views_picture),
                        0
                    ).label("views_picture"),
                    func.coalesce(
                        func.sum(metadata_rank.c.likes),
                        0
                    ).label("likes"),
                    func.coalesce(
                        func.sum(metadata_rank.c.comments_count),
                        0
                    ).label("comments_count"),
                    func.coalesce(
                        func.sum(metadata_rank.c.reposts),
                        0
                    ).label("reposts"),
                    func.coalesce(
                        func.sum(metadata_rank.c.saves),
                        0
                    ).label("saves")
                )
                .join(
                    NetworkItems,
                    NetworkItems._network_id == SocialNetworks.id
                )
                .join(
                    metadata_rank,
                    metadata_rank.c._item_id == NetworkItems.id
                )
                .where(
                    metadata_rank.c.rn == 1
                )
                .where(
                    NetworkItems.published_at >= date_from
                )
                .group_by(
                    SocialNetworks.id
                )
                .order_by(
                    desc(
                        func.sum(
                            metadata_rank.c.views_video +
                            metadata_rank.c.views_picture
                        )
                    )
                )
                .limit(5)
            )
            rows = result.all()
            return [
                {
                    "username": row.username,
                    "type": row.type,
                    "views_video": int(row.views_video or 0),
                    "views_picture": int(row.views_picture or 0),
                    "likes": int(row.likes or 0),
                    "comments_count": int(row.comments_count or 0),
                    "reposts": int(row.reposts or 0),
                    "saves": int(row.saves or 0)
                }
                for row in rows
            ]

    async def get_anomalies(self):
        date_now = datetime.utcnow()
        date_week = date_now - timedelta(days=7)
        date_month = date_now - timedelta(days=30)

        async with get_session() as session:

            metadata_rank = (
                select(
                    ItemMetadata._item_id,
                    ItemMetadata.likes,
                    ItemMetadata.views_picture,
                    ItemMetadata.views_video,
                    ItemMetadata.saves,
                    ItemMetadata.reposts,
                    ItemMetadata.comments_count,
                    func.row_number().over(
                        partition_by=ItemMetadata._item_id,
                        order_by=ItemMetadata.created_at.desc()
                    ).label("rn")
                )
            ).subquery()

            current = (
                select(
                    SocialNetworks.id.label("network_id"),
                    SocialNetworks.username,
                    SocialNetworks.type,
                    func.sum(metadata_rank.c.views_video + metadata_rank.c.views_picture).label("views"),
                    func.sum(metadata_rank.c.likes).label("likes"),
                    func.sum(metadata_rank.c.comments_count).label("comments_count")
                )
                .join(NetworkItems, NetworkItems._network_id == SocialNetworks.id)
                .join(metadata_rank, metadata_rank.c._item_id == NetworkItems.id)
                .where(metadata_rank.c.rn == 1)
                .where(NetworkItems.published_at >= date_week)
                .group_by(SocialNetworks.id)
            ).subquery()

            average = (
                select(
                    SocialNetworks.id.label("network_id"),
                    func.avg(metadata_rank.c.views_video + metadata_rank.c.views_picture).label("avg_views"),
                    func.avg(metadata_rank.c.likes).label("avg_likes"),
                    func.avg(metadata_rank.c.comments_count).label("avg_comments")
                )
                .join(NetworkItems, NetworkItems._network_id == SocialNetworks.id)
                .join(metadata_rank, metadata_rank.c._item_id == NetworkItems.id)
                .where(metadata_rank.c.rn == 1)
                .where(NetworkItems.published_at >= date_month)
                .group_by(SocialNetworks.id)
            ).subquery()

            result = await session.execute(
                select(
                    current.c.username,
                    current.c.type,
                    current.c.views,
                    current.c.likes,
                    current.c.comments_count,
                    average.c.avg_views,
                    average.c.avg_likes,
                    average.c.avg_comments
                )
                .outerjoin(average, current.c.network_id == average.c.network_id)
            )

            anomalies = []

            for row in result:
                views = float(row.views or 0)
                likes = float(row.likes or 0)
                comments = float(row.comments_count or 0)

                avg_views = float(row.avg_views or 0)
                avg_likes = float(row.avg_likes or 0)
                avg_comments = float(row.avg_comments or 0)

                views_factor = views / avg_views if avg_views > 0 else 0
                likes_factor = likes / avg_likes if avg_likes > 0 else 0
                comments_factor = comments / avg_comments if avg_comments > 0 else 0

                if (
                        views_factor >= 3 or
                        likes_factor >= 3 or
                        comments_factor >= 3
                ):
                    anomalies.append({
                        "username": row.username,
                        "type": row.type,
                        "views": int(views),
                        "likes": int(likes),
                        "comments_count": int(comments),
                        "avg_views": int(avg_views),
                        "avg_likes": int(avg_likes),
                        "avg_comments": int(avg_comments),
                        "views_factor": round(views_factor, 2),
                        "likes_factor": round(likes_factor, 2),
                        "comments_factor": round(comments_factor, 2)
                    })

            return anomalies
