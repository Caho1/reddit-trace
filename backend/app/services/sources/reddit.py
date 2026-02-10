from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.reddit_crawler_service import RedditCrawler
from app.services.sources.base import SourceAdapter


class RedditAdapter(SourceAdapter):
    source = "reddit"
    display_name = "Reddit"

    def __init__(self):
        self._crawler = RedditCrawler()

    def capabilities(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "display_name": self.display_name,
            "target_types": ["subreddit", "post_url"],
            "sorts": ["hot", "new", "top", "rising"],
        }

    def normalize_target_key(self, target_type: str, target_key: str) -> str:
        key = (target_key or "").strip()
        if target_type == "subreddit" and key.lower().startswith("r/"):
            key = key[2:]
        return key

    async def fetch_target_items(
        self,
        *,
        target_type: str,
        target_key: str,
        limit: int,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        options = options or {}
        limit = min(max(1, int(limit)), 100)

        if target_type == "subreddit":
            sort = str(options.get("sort") or "hot")
            posts = await self._crawler.fetch_subreddit(target_key, sort=sort, limit=limit)
            return [self._normalize_post(item, target_key=target_key) for item in posts]

        if target_type == "post_url":
            post_url = target_key
            post_result = await self._crawler.fetch_post(post_url)
            post = self._normalize_post(post_result.get("post") or {}, target_key="")
            post["comments"] = [self._normalize_comment(c) for c in (post_result.get("comments") or [])]
            return [post]

        raise ValueError(f"Unsupported Reddit target_type: {target_type}")

    async def fetch_item_comments(
        self,
        *,
        item_external_id: str,
        item_url: Optional[str],
        limit: int,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        url = item_url or f"https://www.reddit.com/comments/{item_external_id}"
        result = await self._crawler.fetch_post(url)
        comments = [self._normalize_comment(c) for c in (result.get("comments") or [])]
        return comments[: max(1, int(limit))]

    async def close(self):
        await self._crawler.close()

    def _normalize_post(self, item: Dict[str, Any], *, target_key: str) -> Dict[str, Any]:
        created_at = item.get("created_utc")
        if isinstance(created_at, datetime):
            created = created_at
        else:
            created = datetime.utcnow()

        permalink = item.get("permalink") or ""
        url = item.get("url")
        if permalink and not str(permalink).startswith("http"):
            permalink_url = f"https://www.reddit.com{permalink}"
        else:
            permalink_url = permalink or url

        return {
            "source": "reddit",
            "external_id": str(item.get("id") or ""),
            "item_type": "post",
            "title": str(item.get("title") or ""),
            "content": item.get("selftext") or None,
            "author": item.get("author") or "[deleted]",
            "url": permalink_url or url,
            "score": int(item.get("score") or 0),
            "num_comments": int(item.get("num_comments") or 0),
            "created_at": created,
            "tags": [item.get("link_flair_text")] if item.get("link_flair_text") else [],
            "payload": item,
            "channel": target_key,
        }

    def _normalize_comment(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        created_at = comment.get("created_utc")
        if isinstance(created_at, datetime):
            created = created_at
        else:
            created = datetime.utcnow()

        return {
            "source": "reddit",
            "external_id": str(comment.get("id") or ""),
            "content": str(comment.get("body") or ""),
            "author": comment.get("author") or "[deleted]",
            "score": int(comment.get("score") or 0),
            "depth": int(comment.get("depth") or 0),
            "parent_external_id": self._parse_parent_external_id(comment.get("parent_id")),
            "created_at": created,
            "payload": comment,
        }

    @staticmethod
    def _parse_parent_external_id(parent_id: Any) -> Optional[str]:
        if isinstance(parent_id, str) and parent_id.startswith("t1_"):
            return parent_id[3:]
        return None
