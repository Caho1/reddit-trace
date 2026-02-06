"""
Reddit 数据抓取服务
使用 Reddit JSON API 抓取帖子和评论数据
"""

import asyncio
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.logging_config import get_logger

logger = get_logger("reddit_trace.crawler")


class RedditCrawler:
    """Reddit 数据抓取器"""

    BASE_URL = "https://www.reddit.com"
    OAUTH_BASE_URL = "https://oauth.reddit.com"
    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
    # 使用更完整的 User-Agent，模拟真实浏览器
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Rate limit 配置
    REQUEST_DELAY = 2.0  # 请求间隔（秒）
    MAX_RETRIES = 2

    def __init__(self):
        self._last_request_time: Optional[float] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._oauth_access_token: Optional[str] = None
        self._oauth_expires_at: Optional[float] = None

    def _oauth_enabled(self) -> bool:
        return bool(settings.reddit_client_id and settings.reddit_client_secret)

    def _get_user_agent(self) -> str:
        return settings.reddit_user_agent or self.USER_AGENT

    def _get_proxy_config(self) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        proxies = {}
        if settings.http_proxy:
            proxies["http://"] = settings.http_proxy
        if settings.https_proxy:
            proxies["https://"] = settings.https_proxy
        elif settings.http_proxy:
            proxies["https://"] = settings.http_proxy

        if proxies:
            logger.debug(f"使用代理配置: {list(proxies.keys())}")
        else:
            logger.debug("未配置代理")
        return proxies if proxies else None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            logger.debug("创建新的 HTTP 客户端...")
            proxy_config = self._get_proxy_config()
            self._client = httpx.AsyncClient(
                headers={"User-Agent": self._get_user_agent()},
                proxy=proxy_config.get("https://") if proxy_config else None,
                timeout=30.0,
                follow_redirects=True,
            )
            logger.debug("HTTP 客户端创建完成")
        return self._client

    async def _get_oauth_token(self) -> Optional[str]:
        """获取 OAuth access_token（Application-only OAuth）"""
        if not self._oauth_enabled():
            return None

        now = time.time()
        if self._oauth_access_token and self._oauth_expires_at and now < self._oauth_expires_at:
            return self._oauth_access_token

        client = await self._get_client()
        logger.info("[OAuth] 获取 Reddit access_token...")
        resp = await client.post(
            self.TOKEN_URL,
            auth=(settings.reddit_client_id, settings.reddit_client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": self._get_user_agent()},
        )
        resp.raise_for_status()
        payload = resp.json()
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))
        if not token:
            raise ValueError("Reddit OAuth 响应缺少 access_token")

        # 预留 60 秒缓冲，避免临界过期
        self._oauth_access_token = token
        self._oauth_expires_at = now + max(0, expires_in - 60)
        logger.info("[OAuth] access_token 获取成功")
        return token

    async def _get_request_headers(self, *, oauth: bool) -> Dict[str, str]:
        if not oauth:
            return {}

        token = await self._get_oauth_token()
        if not token:
            return {}
        return {"Authorization": f"bearer {token}"}

    async def _rate_limit(self):
        """遵守 rate limit，添加请求延迟"""
        if self._last_request_time is not None:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self.REQUEST_DELAY:
                await asyncio.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _fetch_json(self, url: str, *, oauth: bool = False) -> Dict[str, Any]:
        """发送请求并获取 JSON 数据"""
        await self._rate_limit()

        # 未认证模式：尽量使用 .json 端点；认证模式：走 oauth.reddit.com（无需 .json）
        if not oauth:
            if ".json" not in url.split("?")[0]:
                url = url.rstrip("/") + ".json"

        logger.info(f"[HTTP] 请求 URL: {url}")

        client = await self._get_client()
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                headers = await self._get_request_headers(oauth=oauth)
                logger.debug("[HTTP] 发送 GET 请求...")
                response = await client.get(url, headers=headers, params={"raw_json": 1})
                logger.info(f"[HTTP] 响应状态码: {response.status_code}")

                # OAuth token 过期/失效：清空并重试一次
                if oauth and response.status_code == 401 and attempt < self.MAX_RETRIES:
                    logger.warning("[OAuth] access_token 可能已失效，刷新后重试...")
                    self._oauth_access_token = None
                    self._oauth_expires_at = None
                    continue

                response.raise_for_status()

                data = response.json()
                logger.debug(f"[HTTP] 成功获取 JSON 数据")
                return data
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < self.MAX_RETRIES:
                    backoff = 1.0 * (2 ** attempt)
                    logger.warning(
                        f"[HTTP] 连接/超时异常，将重试 (attempt={attempt + 1}/{self.MAX_RETRIES}): {repr(e)}"
                    )
                    await asyncio.sleep(backoff)
                    continue
                if isinstance(e, httpx.ConnectError):
                    logger.error(f"[HTTP] 连接失败 (检查代理配置): {repr(e)}")
                else:
                    logger.error(f"[HTTP] 请求超时: {url}")
                raise
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 429 and attempt < self.MAX_RETRIES:
                    backoff = 2.0 * (2 ** attempt)
                    logger.warning(
                        f"[HTTP] 触发限流 429，将等待并重试 (attempt={attempt + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(backoff)
                    continue
                logger.error(f"[HTTP] HTTP 错误 {status}: {url}")
                raise
            except Exception as e:
                logger.error(f"[HTTP] 请求异常: {type(e).__name__}: {e}")
                raise

        raise RuntimeError("unreachable")

    def _to_oauth_url(self, url: str) -> Optional[str]:
        """将常见 Reddit URL 转换为 oauth.reddit.com 请求 URL"""
        if not self._oauth_enabled():
            return None

        try:
            u = httpx.URL(url)
        except Exception:
            return None

        host = (u.host or "").lower()
        path = u.path or "/"

        # 已经是 oauth 域名
        if host.endswith("oauth.reddit.com"):
            return str(u.copy_set_param("raw_json", "1"))

        # 短链：https://redd.it/<id>
        if host.endswith("redd.it"):
            post_id = path.strip("/").split("/")[0]
            if post_id:
                oauth_url = httpx.URL(f"{self.OAUTH_BASE_URL}/comments/{post_id}")
                return str(oauth_url.copy_set_param("raw_json", "1"))
            return None

        # 常规域名：复用 path，切到 oauth 域名；去掉 .json
        if host.endswith("reddit.com"):
            if path.endswith(".json"):
                path = path[:-5]
            oauth_url = httpx.URL(f"{self.OAUTH_BASE_URL}{path}")
            # 复制 query（如有）
            for key, value in u.params.multi_items():
                oauth_url = oauth_url.copy_add_param(key, value)
            oauth_url = oauth_url.copy_set_param("raw_json", "1")
            return str(oauth_url)

        return None

    def _parse_comment(self, comment_data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """解析单个评论数据"""
        data = comment_data.get("data", {})

        return {
            "id": data.get("id"),
            "author": data.get("author"),
            "body": data.get("body"),
            "score": data.get("score", 0),
            "created_utc": datetime.fromtimestamp(data.get("created_utc", 0), tz=timezone.utc),
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
        logger.info(f"[Post] 开始抓取帖子: {url}")

        try:
            logger.info("[Post] 步骤 1/3: 获取帖子数据...")
            oauth_url = self._to_oauth_url(url)
            if oauth_url:
                logger.info("[Post] 使用 OAuth API 抓取")
                data = await self._fetch_json(oauth_url, oauth=True)
            else:
                data = await self._fetch_json(url, oauth=False)
            logger.info("[Post] 步骤 1/3: 获取成功")

            # Reddit 返回一个包含两个 Listing 的数组
            # 第一个是帖子信息，第二个是评论
            if not isinstance(data, list) or len(data) < 2:
                logger.error("[Post] 响应格式无效")
                raise ValueError("Invalid Reddit post response format")

            # 解析帖子数据
            logger.info("[Post] 步骤 2/3: 解析帖子信息...")
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
                "created_utc": datetime.fromtimestamp(post_data.get("created_utc", 0), tz=timezone.utc),
                "subreddit": post_data.get("subreddit"),
                "permalink": post_data.get("permalink"),
                "url": post_data.get("url"),
                "is_self": post_data.get("is_self", True),
                "link_flair_text": post_data.get("link_flair_text"),
            }
            logger.info(f"[Post] 步骤 2/3: 解析完成 - {post.get('title', 'N/A')[:50]}")

            # 解析评论
            logger.info("[Post] 步骤 3/3: 解析评论...")
            comments_listing = data[1]
            comment_children = comments_listing.get("data", {}).get("children", [])
            comments = self._parse_comments_recursive(comment_children)
            logger.info(f"[Post] 步骤 3/3: 解析完成，共 {len(comments)} 条评论")

            logger.info(f"[Post] 抓取完成!")
            return {
                "post": post,
                "comments": comments,
            }

        except Exception as e:
            logger.error(f"[Post] 抓取失败: {type(e).__name__}: {e}")
            raise

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
        name = (name or "").strip()
        if name.lower().startswith("r/"):
            name = name[2:].strip()

        logger.info(f"[Subreddit] 开始抓取 r/{name} (sort={sort}, limit={limit})")

        # 验证排序方式
        valid_sorts = ["hot", "new", "top", "rising"]
        if sort not in valid_sorts:
            logger.warning(f"[Subreddit] 无效排序方式 '{sort}'，使用默认 'hot'")
            sort = "hot"

        # 限制数量范围
        limit = min(max(1, limit), 100)

        if self._oauth_enabled():
            url = f"{self.OAUTH_BASE_URL}/r/{name}/{sort}?limit={limit}"
        else:
            url = f"{self.BASE_URL}/r/{name}/{sort}.json?limit={limit}"

        try:
            logger.info(f"[Subreddit] 步骤 1/2: 获取帖子列表...")
            data = await self._fetch_json(url, oauth=self._oauth_enabled())
            logger.info(f"[Subreddit] 步骤 1/2: 获取成功")

            # 解析帖子列表
            logger.info(f"[Subreddit] 步骤 2/2: 解析帖子数据...")
            posts = []
            children = data.get("data", {}).get("children", [])
            logger.debug(f"[Subreddit] 获取到 {len(children)} 条原始数据")

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
                    "created_utc": datetime.fromtimestamp(post_data.get("created_utc", 0), tz=timezone.utc),
                    "subreddit": post_data.get("subreddit"),
                    "permalink": post_data.get("permalink"),
                    "url": post_data.get("url"),
                    "is_self": post_data.get("is_self", True),
                    "link_flair_text": post_data.get("link_flair_text"),
                    "thumbnail": post_data.get("thumbnail"),
                })

            logger.info(f"[Subreddit] 步骤 2/2: 解析完成，共 {len(posts)} 个帖子")
            logger.info(f"[Subreddit] 抓取 r/{name} 完成!")
            return posts

        except Exception as e:
            logger.error(f"[Subreddit] 抓取 r/{name} 失败: {type(e).__name__}: {e}")
            raise

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
