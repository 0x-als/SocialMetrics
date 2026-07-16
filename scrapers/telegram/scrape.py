import os
import json
import httpx
import asyncio

from config import base_dir
from utils import security
from config import base_dir
from database import init_database
from telethon import TelegramClient
from utils.logger import logger_config
from datetime import timezone, datetime, UTC


class ScraperTelegramURL:
    def __init__(self):
        self.log_file = "ScraperTelegramURL.log"
        self.urls = []
        self.metadata_delay = 3
        self.session = None
        self.results = []

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)
        try:
            urls = await init_database.social_networks_repo.get_social_networks_by_type("telegram")
            if not urls:
                logger.warning("No telegram channels found")
                self.urls = []
                return
            urls_active = [u for u in urls if u.status]
            logger.info(f"Loaded {len(urls_active)} telegram channels")
            self.urls = urls_active
            return self.urls
        except Exception as ex:
            logger.exception(ex)

    async def _load_session(self):
        logger = logger_config(name="_load_session", log_file=self.log_file)
        try:
            sessions = await init_database.scrape_accounts_repo.get_scrape_account_by_type("telegram")
            if not sessions:
                logger.warning("No telegram sessions found")
                return False

            sess = sessions[0]
            api_id = int(await security.decrypt(sess.api_key))
            api_hash = await security.decrypt(sess.token_hash)
            session_name = sess.path

            session_dir = os.path.join(base_dir, "files", "profiles", "telegram_profile")
            session_path = os.path.join(session_dir, session_name)

            self.session = TelegramClient(session_path, api_id, api_hash)
            await self.session.connect()

            if not await self.session.is_user_authorized():
                logger.warning("Telegram session not authorized")
                return False

            logger.info(f"Telegram session loaded: {session_path}")
            return True
        except Exception as ex:
            logger.exception(ex)
            return False

    async def run(self):
        logger = logger_config(name="run", log_file=self.log_file)
        try:
            await self._load_urls()
            if not self.urls:
                return

            if not await self._load_session():
                return

            for url_object in self.urls:
                channel_url = url_object.url
                logger.info(f"Processing channel: {channel_url}")

                try:
                    entity = await self.session.get_entity(channel_url)
                    count = 0

                    async for message in self.session.iter_messages(entity, limit=None):
                        if message.text or message.photo or message.video:
                            msg_url = f"https://t.me/{entity.username}/{message.id}" if entity.username else f"https://t.me/c/{entity.id}/{message.id}"
                            published_at = None
                            if message.date:
                                dt = message.date
                                if isinstance(dt, str):
                                    dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                                if dt.tzinfo is not None:
                                    dt = dt.replace(tzinfo=None)
                                published_at = dt
                            self.results.append({
                                "network_item_id": url_object.id,
                                "url": msg_url,
                                "title": message.text[:200] if message.text else "",
                                "published_at": published_at,
                            })
                            count += 1

                            if count % 50 == 0:
                                logger.info(f"Collected {count} messages from {channel_url}")

                    logger.info(f"Collected total {count} messages from {channel_url}")

                except Exception as ex:
                    logger.warning(f"Error processing {channel_url}: {ex}")

                await asyncio.sleep(self.metadata_delay)

            if self.results:
                logger.info(f"Total collected {len(self.results)} Telegram items. Saving...")
                await init_database.telegram_repo.save_network_items(self.results)

        except Exception as ex:
            logger.exception(ex)
        finally:
            if self.session:
                await self.session.disconnect()


class ScraperTelegramMetadata:
    def __init__(self):
        self.log_file = "ScraperTelegramMetadata.log"
        self.urls = []
        self.sessions = []
        self.results = []
        self.metadata_delay = 3
        self.batch_size = 200

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)
        try:
            self.urls = await init_database.network_item_repo.get_network_items_by_type("telegram")
            if not self.urls:
                logger.warning("No work urls found!")
                self.urls = []
                return []
            urls_active = [u for u in self.urls if u.status]
            logger.info(f"Found {len(urls_active)} active urls")
            self.urls = urls_active
            return self.urls
        except Exception as ex:
            logger.exception(ex)

    async def _load_sessions(self):
        logger = logger_config(name="_load_sessions", log_file=self.log_file)
        try:
            db_sessions = await init_database.scrape_accounts_repo.get_scrape_account_by_type("telegram")
            if db_sessions:
                for sess in db_sessions:
                    api_id = int(await security.decrypt(sess.api_key))
                    api_hash = await security.decrypt(sess.token_hash)
                    session_name = sess.path
                    session_dir = os.path.join(base_dir, "files", "profiles", "telegram_profile")
                    os.makedirs(session_dir, exist_ok=True)
                    session_path = os.path.join(session_dir, session_name)
                    self.sessions.append({"api_id": api_id, "api_hash": api_hash, "session_path": session_path})
                logger.info(f"Loaded {len(self.sessions)} sessions")
            else:
                logger.warning("No sessions found")
                self.sessions = []
        except Exception as ex:
            logger.exception(ex)

    def _normalize_metadata(self, raw_metadata):
        if not isinstance(raw_metadata, dict):
            return {"success": False, "error": "Invalid metadata format"}

        published_at = raw_metadata.get("published_at")
        if published_at and isinstance(published_at, datetime):
            try:
                published_at = published_at.strftime("%Y-%m-%d %H:%M:%S")
            except:
                published_at = None

        normalized = {
            "likes": int(raw_metadata.get("views") or 0),
            "video_views_count": int(raw_metadata.get("views") or 0),
            "video_play_count": int(raw_metadata.get("views") or 0),
            "comments_count": int(raw_metadata.get("replies") or 0),
            "shares": int(raw_metadata.get("forwards") or 0),
            "saves": 0,
            "published_at": published_at,
            "caption": "",
            "followers": None
        }
        return normalized

    async def _fetch_metadata(self, client, message_id, channel):
        try:
            message = await client.get_messages(channel, ids=message_id)
            if not message:
                return None
            return {
                "views": message.views or 0,
                "forwards": message.forwards or 0,
                "replies": message.replies.replies if message.replies else 0,
                "published_at": message.date.replace(tzinfo=None) if message.date else None
            }
        except Exception:
            return None

    async def _process_batch(self, batch, session_info):
        results = []
        logger = logger_config(name="_process_batch", log_file=self.log_file)

        try:
            client = TelegramClient(session_info["session_path"], session_info["api_id"], session_info["api_hash"])
            await client.connect()
            if not await client.is_user_authorized():
                await client.disconnect()
                return results

            for url_object in batch:
                url = url_object.url
                logger.info(f"Processing URL: {url}")

                try:
                    parts = url.split("/")
                    channel_part = parts[-2] if len(parts) > 2 else None
                    message_id = int(parts[-1])

                    entity = await client.get_entity(channel_part)
                    raw_metadata = await self._fetch_metadata(client, message_id, entity)

                    if raw_metadata:
                        normalized = self._normalize_metadata(raw_metadata)
                        results.append({
                            "network_item_id": url_object.id,
                            "url": url,
                            "metadata": normalized
                        })
                        logger.info(f"Successfully fetched metadata for {url}")
                except Exception:
                    logger.info(f"Failed to fetch metadata for {url}")
                    continue

            await client.disconnect()
        except Exception as ex:
            logger.exception(ex)
        return results

    async def run(self):
        logger = logger_config(name="run", log_file=self.log_file)
        try:
            await self._load_urls()
            await self._load_sessions()

            logger.info(f"Starting processing of {len(self.urls)} URLs with {len(self.sessions)} sessions")

            if not self.urls or not self.sessions:
                logger.warning("Нет URL или сессий для обработки")
                return

            data_metadata = []

            if len(self.sessions) > 1:
                tasks = []
                chunk_size = max(1, len(self.urls) // len(self.sessions) + 1)
                for i in range(0, len(self.urls), chunk_size):
                    batch = self.urls[i:i + chunk_size]
                    session = self.sessions[i % len(self.sessions)]
                    tasks.append(self._process_batch(batch, session))

                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r in results:
                    if isinstance(r, list):
                        data_metadata.extend(r)
                    elif isinstance(r, Exception):
                        logger.exception(r)
            else:
                batch_results = await self._process_batch(self.urls, self.sessions[0])
                data_metadata.extend(batch_results)

            if data_metadata:
                logger.info(f"Successfully processed {len(data_metadata)} items. Saving to database.")
                await init_database.item_metadata_repo.save_metadata(data_metadata)
                await init_database.network_item_repo.update_published_at(data_metadata)
            else:
                logger.info("No metadata was collected.")

        except Exception as ex:
            logger.exception(ex)
