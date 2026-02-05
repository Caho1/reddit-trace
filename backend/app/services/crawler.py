"""
Reddit 数据抓取服务
使用 Reddit JSON API 抓取帖子和评论数据
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

import httpx

from app.config import settings


class RedditCrawler:
    """Reddit 数据抓取器"""

    BASE_URL = "https://www.reddit.com"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Rate limit 配置
    REQUEST_DELAY = 2.0  # 请求间隔（秒）

    def __init__(self):
        self._last_request_time: Optional[float] = None
        self._client: Optional[httpx.AsyncClient] = None

    def _get_proxy_config(self) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        proxies = {}
        if settings.http_proxy:
            proxies["http://"] = settings.http_proxy
        if settings.https_proxy:
            proxies["https://"] = settings.https_proxy
        elif settings.http_proxy:
            proxies["https://"] = settings.http_proxy
        return proxies if proxies else None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            proxy_config = self._get_proxy_config()
            self._client = httpx.AsyncClient(
                headers={"User-Agent": self.USER_AGENT},
                proxy=proxy_config.get("https://") if proxy_config else None,
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def _rate_limit(self):
        """遵守 rate limit，添加请求延迟"""
        if self._last_request_time is not None:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self.REQUEST_DELAY:
                await asyncio.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _fetch_json(self, url: str) -> Dict[str, Any]:
        """发送请求并获取 JSON 数据"""
        await self._rate_limit()

        # 确保 URL 以 .json 结尾
        if not url.endswith(".json"):
            url = url.rstrip("/") + "/.json"

        client = await self._get_client()
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    def _parse_comment(self, comment_data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """解析单个评论数据"""
        data = comment_data.get("data", {})

        return {
            "id": data.get("id"),
            "author": data.get("author"),
            "body": data.get("body"),
            "score": data.get("score", 0),
            "created_utc": datetime.fromtimestamp(data.get("created_utc", 0)),
            "permalink": data.get("permalink"),
            "depth": depth,
            "parent_id": data.get("parent_id"),
            "is_submitter": data.get("is_submitter", False),
        }

    def _parse_comments_recursive(
        self, children: List[Dict[str, Any]], depth: int = 0
    ) -> List[Dict[str, Any]]:
        """递归解析嵌套评论结构"""
        comments = []

        for child in children:
            kind = child.get("kind")

            # 跳过 "more" 类型（加载更多评论的占位符）
            if kind == "more":
                continue

            if kind == "t1":  # t1 表示评论
                comment = self._parse_comment(child, depth)
                comments.append(comment)

                # 递归解析回复
                replies = child.get("data", {}).get("replies")
                if replies and isinstance(replies, dict):
                    reply_children = replies.get("data", {}).get("children", [])
                    comments.extend(
                        self._parse_comments_recursive(reply_children, depth + 1)
                    )

        return comments

    async def fetch_post(self, url: str) -> dict:
        """
        抓取单个帖子及其评论

        Args:
            url: Reddit 帖子 URL

        Returns:
            包含帖子信息和评论列表的字典
        """
        data = await self._fetch_json(url)

        # Reddit 返回一个包含两个 Listing 的数组
        # 第一个是帖子信息，第二个是评论
        if not isinstance(data, list) or len(data) < 2:
            raise ValueError("Invalid Reddit post response format")

        # 解析帖子数据
        post_listing = data[0]
        post_data = post_listing.get("data", {}).get("children", [{}])[0].get("data", {})

        post = {
            "id": post_data.get("id"),
            "title": post_data.get("title"),
            "author": post_data.get("author"),
            "selftext": post_data.get("selftext"),
            "score": post_data.get("score", 0),
            "upvote_ratio": post_data.get("upvote_ratio", 0),
            "num_comments": post_data.get("num_comments", 0),
            "created_utc": datetime.fromtimestamp(post_data.get("created_utc", 0)),
            "subreddit": post_data.get("subreddit"),
            "permalink": post_data.get("permalink"),
            "url": post_data.get("url"),
            "is_self": post_data.get("is_self", True),
            "link_flair_text": post_data.get("link_flair_text"),
        }

        # 解析评论
        comments_listing = data[1]
        comment_children = comments_listing.get("data", {}).get("children", [])
        comments = self._parse_comments_recursive(comment_children)

        return {
            "post": post,
            "comments": comments,
        }

    async def fetch_subreddit(
        self, name: str, sort: str = "hot", limit: int = 25
    ) -> List[dict]:
        """
        抓取版块帖子列表

        Args:
            name: 版块名称（不含 r/ 前缀）
            sort: 排序方式 (hot, new, top, rising)
            limit: 返回帖子数量限制（最大 100）

        Returns:
            帖子列表
        """
        # 验证排序方式
        valid_sorts = ["hot", "new", "top", "rising"]
        if sort not in valid_sorts:
            sort = "hot"

        # 限制数量范围
        limit = min(max(1, limit), 100)

        url = f"{self.BASE_URL}/r/{name}/{sort}.json?limit={limit}"
        data = await self._fetch_json(url)

        # 解析帖子列表
        posts = []
        children = data.get("data", {}).get("children", [])

        for child in children:
            if child.get("kind") != "t3":  # t3 表示帖子
                continue

            post_data = child.get("data", {})
            posts.append({
                "id": post_data.get("id"),
                "title": post_data.get("title"),
                "author": post_data.get("author"),
                "selftext": post_data.get("selftext"),
                "score": post_data.get("score", 0),
                "upvote_ratio": post_data.get("upvote_ratio", 0),
                "num_comments": post_data.get("num_comments", 0),
                "created_utc": datetime.fromtimestamp(post_data.get("created_utc", 0)),
                "subreddit": post_data.get("subreddit"),
                "permalink": post_data.get("permalink"),
                "url": post_data.get("url"),
                "is_self": post_data.get("is_self", True),
                "link_flair_text": post_data.get("link_flair_text"),
                "thumbnail": post_data.get("thumbnail"),
            })

        return posts

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """支持 async with 语法"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出时自动关闭客户端"""
        await self.close()


# 创建全局实例供外部使用
crawler = RedditCrawler()
