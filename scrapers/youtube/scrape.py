import os
import json
import httpx
import asyncio

from utils import security
from config import base_dir
from database import init_database
from utils.logger import logger_config
from datetime import timezone, datetime, UTC


class ScraperYoutubeURL:
    def __init__(self):
        self.log_file = "ScraperYoutubeURL.log"
        self.urls = []
        self.metadata_delay = 3
        self.sessions = []
        self.results = []

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)
        try:
            urls = await init_database.social_networks_repo.get_social_networks_by_type("youtube")
            if not urls:
                logger.warning("No youtube accounts found")
                self.urls = []
                return
            urls_active = [u for u in urls if u.status]
            logger.info(f"Loaded {len(urls_active)} youtube accounts")
            self.urls = urls_active
            return self.urls
        except Exception as ex:
            logger.exception(ex)

    async def _load_sessions(self):
        logger = logger_config(name="_load_sessions", log_file=self.log_file)
        try:
            sessions = await init_database.scrape_accounts_repo.get_scrape_account_by_type("youtube")
            if not sessions:
                logger.warning("No youtube sessions found")
                self.sessions = []
                return
            for session in sessions:
                api_key = await security.decrypt(session.api_key)
                if api_key:
                    self.sessions.append({"api_key": api_key})
            logger.info(f"Loaded {len(self.sessions)} sessions")
        except Exception as ex:
            logger.exception(ex)

    async def _get_channel_id(self, channel_url: str, api_key: str):
        logger = logger_config(name="_get_channel_id", log_file=self.log_file)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if "@" in channel_url:
                    handle = channel_url.split("@")[-1].strip("/")
                    params = {"part": "id", "forHandle": handle, "key": api_key}
                    response = await client.get("https://www.googleapis.com/youtube/v3/channels", params=params)
                else:
                    params = {"part": "id", "key": api_key}
                    response = await client.get("https://www.googleapis.com/youtube/v3/channels", params=params)
                data = response.json()
                if data.get("items"):
                    return data["items"][0]["id"]
                logger.warning(f"Failed to get channel ID for {channel_url}")
                return None
        except Exception as ex:
            logger.exception(ex)
            return None

    async def _fetch_videos(self, channel_id: str, api_key: str, video_type: str = "videos"):
        logger = logger_config(name="_fetch_videos", log_file=self.log_file)
        videos = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {"part": "contentDetails", "id": channel_id, "key": api_key}
                response = await client.get("https://www.googleapis.com/youtube/v3/channels", params=params)
                data = response.json()
                if not data.get("items"):
                    return []
                uploads_playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

                next_page_token = None
                while True:
                    params = {"part": "snippet,contentDetails", "playlistId": uploads_playlist_id, "maxResults": 50, "key": api_key}
                    if next_page_token:
                        params["pageToken"] = next_page_token
                    response = await client.get("https://www.googleapis.com/youtube/v3/playlistItems", params=params)
                    data = response.json()

                    for item in data.get("items", []):
                        video_id = item["contentDetails"]["videoId"]
                        title = item["snippet"]["title"]
                        published_at = item["snippet"]["publishedAt"]

                        if video_type == "shorts" and not title.lower().startswith("#shorts") and not self._is_short(item):
                            continue
                        if video_type == "videos" and self._is_short(item):
                            continue

                        videos.append({
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "title": title,
                            "published_at": published_at,
                            "video_id": video_id,
                            "channel_id": channel_id
                        })

                    next_page_token = data.get("nextPageToken")
                    if not next_page_token:
                        break
                    await asyncio.sleep(0.5)
            return videos
        except Exception as ex:
            logger.exception(ex)
            return []

    def _is_short(self, item):
        title = item.get("snippet", {}).get("title", "").lower()
        return "#short" in title or "shorts" in item.get("snippet", {}).get("thumbnails", {}).get("default", {}).get("url", "")

    async def run(self):
        logger = logger_config(name="run", log_file=self.log_file)
        try:
            await self._load_urls()
            await self._load_sessions()

            if not self.urls:
                logger.warning("Нет YouTube каналов для обработки")
                return
            if not self.sessions:
                logger.warning("Нет API ключей для YouTube")
                return

            logger.info(f"Starting video collection for {len(self.urls)} channels with {len(self.sessions)} sessions")

            for url_object in self.urls:
                channel_url = url_object.url
                logger.info(f"Processing channel: {channel_url}")

                api_key = self.sessions[0].get("api_key")
                if not api_key:
                    continue

                channel_id = await self._get_channel_id(channel_url, api_key)
                if not channel_id:
                    logger.warning(f"Could not get channel ID for {channel_url}")
                    continue

                logger.info(f"Got channel ID: {channel_id}")

                regular_videos = await self._fetch_videos(channel_id, api_key, video_type="videos")
                shorts = await self._fetch_videos(channel_id, api_key, video_type="shorts")

                all_items = regular_videos + shorts
                profile_data = {
                    "id": url_object.id,
                    "url": channel_url,
                    "urls": [item["url"] for item in all_items]
                }
                self.results.append([profile_data])

                logger.info(f"Collected {len(regular_videos)} videos and {len(shorts)} shorts for {channel_url}")
                await asyncio.sleep(self.metadata_delay)

            if self.results:
                logger.info(f"Total collected {len(self.results)} items. Saving...")
                await init_database.youtube_repo.save_network_items(self.results)
        except Exception as ex:
            logger.exception(ex)


class ScraperYoutubeMetadata:
    def __init__(self):
        self.log_file = "ScraperYoutubeMetadata.log"
        self.urls = []
        self.sessions = []
        self.results = []
        self.metadata_delay = 3
        self.batch_size = 200

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)
        try:
            self.urls = await init_database.network_item_repo.get_network_items_by_type("youtube")
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
            sessions = await init_database.scrape_accounts_repo.get_scrape_account_by_type("youtube")
            if sessions:
                for session in sessions:
                    api_key = await security.decrypt(session.api_key)
                    if api_key:
                        self.sessions.append({"api_key": api_key})
                logger.info(f"Loaded {len(self.sessions)} sessions")
            else:
                logger.warning("No sessions found")
                self.sessions = []
        except Exception as ex:
            logger.exception(ex)

    def _normalize_metadata(self, raw_metadata):
        if not isinstance(raw_metadata, dict):
            return {"success": False, "error": "Invalid metadata format"}

        published_at = raw_metadata.get("publishedAt")
        if published_at:
            try:
                dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                published_at = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                published_at = None

        normalized = {
            "likes": int(raw_metadata.get("likeCount") or 0),
            "video_views_count": int(0),
            "video_play_count": int(raw_metadata.get("viewCount") or 0),
            "comments_count": int(raw_metadata.get("commentCount") or 0),
            "shares": 0,
            "saves": 0,
            "published_at": published_at,
            "caption": raw_metadata.get("title"),
            "followers": None
        }
        return normalized

    async def _fetch_metadata(self, api_key: str, video_id: str):
        logger = logger_config(name="_fetch_metadata", log_file=self.log_file)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {
                    "part": "statistics,snippet",
                    "id": video_id,
                    "key": api_key
                }
                response = await client.get("https://www.googleapis.com/youtube/v3/videos", params=params)
                data = response.json()

                if not data.get("items"):
                    return None

                item = data["items"][0]
                stats = item.get("statistics", {})
                snippet = item.get("snippet", {})

                return {
                    "likeCount": stats.get("likeCount"),
                    "viewCount": stats.get("viewCount"),
                    "commentCount": stats.get("commentCount"),
                    "publishedAt": snippet.get("publishedAt"),
                    "title": snippet.get("title")
                }
        except Exception as ex:
            logger.exception(ex)
            return None

    async def _process_batch(self, batch, sessions):
        results = []
        logger = logger_config(name="_process_batch", log_file=self.log_file)

        for url_object in batch:
            url = url_object.url
            logger.info(f"Processing URL: {url}")

            try:
                video_id = url.split("v=")[-1].split("&")[0]
            except:
                logger.info(f"Failed to extract video_id for {url}")
                continue

            success = False
            for session in sessions:
                api_key = session.get("api_key")
                if not api_key:
                    continue

                metadata = await self._fetch_metadata(api_key, video_id)
                if metadata:
                    normalized = self._normalize_metadata(metadata)
                    results.append({
                        "network_item_id": url_object.id,
                        "url": url,
                        "metadata": normalized
                    })
                    logger.info(f"Successfully fetched metadata for {url}")
                    success = True
                    break

            if not success:
                logger.info(f"Failed to fetch metadata for {url}")

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
                # Parallel processing
                tasks = []
                chunk_size = max(1, len(self.urls) // len(self.sessions) + 1)
                for i in range(0, len(self.urls), chunk_size):
                    batch = self.urls[i:i + chunk_size]
                    session = self.sessions[i % len(self.sessions)]
                    tasks.append(self._process_batch(batch, [session]))

                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r in results:
                    if isinstance(r, list):
                        data_metadata.extend(r)
                    elif isinstance(r, Exception):
                        logger.exception(r)
            else:
                batch_results = await self._process_batch(self.urls, self.sessions)
                data_metadata.extend(batch_results)

            if data_metadata:
                logger.info(f"Successfully processed {len(data_metadata)} items. Saving to database.")
                await init_database.item_metadata_repo.save_metadata(data_metadata)
                await init_database.network_item_repo.update_published_at(data_metadata)
            else:
                logger.info("No metadata was collected.")

        except Exception as ex:
            logger.exception(ex)
