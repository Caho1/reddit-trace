from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.services.sources.base import SourceAdapter


class HackerNewsAdapter(SourceAdapter):
    source = "hackernews"
    display_name = "Hacker News"
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    def capabilities(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "display_name": self.display_name,
            "target_types": ["feed", "story"],
            "feeds": ["topstories", "newstories", "askstories", "showstories"],
        }

    def normalize_target_key(self, target_type: str, target_key: str) -> str:
        key = (target_key or "").strip().lower()
        if target_type == "feed":
            allowed = {"topstories", "newstories", "askstories", "showstories"}
            if key not in allowed:
                raise ValueError(f"Unsupported Hacker News feed: {target_key}")
            return key
        return (target_key or "").strip()

    async def fetch_target_items(
        self,
        *,
        target_type: str,
        target_key: str,
        limit: int,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        limit = max(1, int(limit))

        if target_type == "feed":
            story_ids = await self._fetch_feed_story_ids(target_key)
            story_ids = story_ids[:limit]
            items: List[Dict[str, Any]] = []
            for sid in story_ids:
                item = await self._fetch_item(sid)
                if item and item.get("type") in {"story", "job"}:
                    items.append(self._normalize_story(item, feed=target_key))
            return items

        if target_type == "story":
            story = await self._fetch_item(int(target_key))
            if not story:
                return []
            normalized = self._normalize_story(story, feed="story")
            return [normalized]

        raise ValueError(f"Unsupported Hacker News target_type: {target_type}")

    async def fetch_item_comments(
        self,
        *,
        item_external_id: str,
        item_url: Optional[str],
        limit: int,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        story = await self._fetch_item(int(item_external_id))
        if not story:
            return []

        kids = story.get("kids") or []
        comments: List[Dict[str, Any]] = []
        for kid in kids[: max(1, int(limit))]:
            comment = await self._fetch_item(int(kid))
            if not comment or comment.get("deleted") or comment.get("dead"):
                continue
            if comment.get("type") != "comment":
                continue
            comments.append(self._normalize_comment(comment))
        return comments

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=20.0, follow_redirects=True)
        return self._client

    async def _fetch_feed_story_ids(self, feed: str) -> List[int]:
        client = await self._get_client()
        resp = await client.get(f"{self.BASE_URL}/{feed}.json")
        resp.raise_for_status()
        data = resp.json() or []
        return [int(x) for x in data]

    async def _fetch_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        client = await self._get_client()
        resp = await client.get(f"{self.BASE_URL}/item/{item_id}.json")
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        return data

    def _normalize_story(self, story: Dict[str, Any], *, feed: str) -> Dict[str, Any]:
        created_at = datetime.fromtimestamp(int(story.get("time") or 0), tz=timezone.utc)
        story_id = str(story.get("id") or "")
        url = story.get("url") or f"https://news.ycombinator.com/item?id={story_id}"
        return {
            "source": self.source,
            "external_id": story_id,
            "item_type": str(story.get("type") or "story"),
            "title": str(story.get("title") or ""),
            "content": story.get("text") or None,
            "author": story.get("by") or "unknown",
            "url": url,
            "score": int(story.get("score") or 0),
            "num_comments": int(story.get("descendants") or 0),
            "created_at": created_at,
            "tags": [],
            "payload": story,
            "channel": feed,
        }

    def _normalize_comment(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        created_at = datetime.fromtimestamp(int(comment.get("time") or 0), tz=timezone.utc)
        return {
            "source": self.source,
            "external_id": str(comment.get("id") or ""),
            "content": str(comment.get("text") or ""),
            "author": comment.get("by") or "unknown",
            "score": 0,
            "depth": 0,
            "parent_external_id": str(comment.get("parent") or "") if comment.get("parent") else None,
            "created_at": created_at,
            "payload": comment,
        }

