from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import httpx

from app.database import get_db
from app.services import crawler
from app.services.reddit_ingestion_service import save_post_comments, save_subreddit_posts
from app.models.posts import Post
from sqlalchemy import select
from app.logging_config import get_logger
from app.services.source_fetch_service import fetch_and_ingest_target
from app.services.source_ingestion_service import upsert_source_target
from app.services.source_registry_service import source_registry

logger = get_logger("reddit_trace.api.crawler")

router = APIRouter()


class FetchRequest(BaseModel):
    """按 URL 抓取单条内容的请求体。"""

    url: str


class FetchSubredditRequest(BaseModel):
    """抓取 subreddit 列表的请求体。"""

    name: str
    sort: str = "hot"
    limit: int = 25


@router.post("/fetch-post")
async def fetch_post(req: FetchRequest, db: AsyncSession = Depends(get_db)):
    """抓取单贴及评论，并写入旧表和统一表。

    参数：
        req: 含帖子 URL 的请求体。
        db: 异步数据库会话。

    返回：
        dict: 抓取结果与入库统计。
    """
    logger.info(f"[API] 收到抓取帖子请求: {req.url}")
    try:
        result = await crawler.fetch_post(req.url)

        fetched_at = datetime.now(timezone.utc)
        post_data = result.get("post") or {}
        comments_data = result.get("comments") or []

        _, post_created, post_updated = await save_subreddit_posts(
            db,
            subreddit_name=post_data.get("subreddit") or "",
            posts=[post_data],
            fetched_at=fetched_at,
        )
        post_reddit_id = post_data.get("id")
        db_post = None
        if post_reddit_id:
            db_post = await db.scalar(select(Post).where(Post.reddit_id == post_reddit_id))

        comment_created = 0
        comment_updated = 0
        if db_post:
            comment_created, comment_updated = await save_post_comments(
                db,
                post=db_post,
                comments=comments_data,
                fetched_at=fetched_at,
            )

        await db.commit()

        # 写入统一模型（source_items/source_comments）
        try:
            await fetch_and_ingest_target(
                db,
                source="reddit",
                target_type="post_url",
                target_key=req.url,
                limit=1,
                include_comments=True,
                comment_limit=max(20, len(comments_data) or 20),
                options={},
            )
        except Exception as ingest_err:
            logger.warning(f"[API] 统一模型写入失败(不影响旧返回): {ingest_err}")

        logger.info(f"[API] 帖子抓取成功")
        return {
            **result,
            "saved": {
                "posts_created": post_created,
                "posts_updated": post_updated,
                "comments_created": comment_created,
                "comments_updated": comment_updated,
            },
        }
    except httpx.TimeoutException:
        logger.error(f"[API] 请求超时: {req.url}")
        raise HTTPException(
            status_code=504,
            detail={
                "error": "TimeoutError",
                "message": "请求 Reddit 超时，请检查网络连接或代理配置",
                "step": "HTTP请求"
            }
        )
    except httpx.ConnectError as e:
        logger.error(f"[API] 连接失败: {repr(e)}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "ConnectError",
                "message": f"无法连接到 Reddit，请检查网络/代理配置: {repr(e)}",
                "step": "HTTP连接"
            }
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"[API] HTTP 错误: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail={
                "error": "HTTPError",
                "message": f"Reddit 返回错误: {e.response.status_code}",
                "step": "HTTP响应"
            }
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"[API] 未知错误: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": type(e).__name__,
                "message": str(e),
                "step": "未知"
            }
        )


@router.post("/fetch-item")
async def fetch_item(req: FetchRequest, db: AsyncSession = Depends(get_db)):
    """统一抓取入口：按 URL 自动识别平台并写入统一表。

    参数：
        req: 目标 URL 请求体。
        db: 异步数据库会话。

    返回：
        dict: 平台信息、抓取结果与入库统计。
    """
    url = (req.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    source = "reddit"
    target_type = "post_url"
    if "news.ycombinator.com/item?id=" in url:
        source = "hackernews"
        target_type = "story"
        try:
            story_id = url.split("item?id=")[1].split("&")[0]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Hacker News story URL")
        target_key = story_id
    else:
        target_key = url

    try:
        source_registry.get(source)
        result = await fetch_and_ingest_target(
            db,
            source=source,
            target_type=target_type,
            target_key=target_key,
            limit=1,
            include_comments=True,
            comment_limit=100,
            options={},
        )
        return {
            "source": source,
            "items": result["items"],
            "saved": result["saved"],
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[API] 统一抓取失败: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-subreddit")
async def fetch_subreddit(req: FetchSubredditRequest, db: AsyncSession = Depends(get_db)):
    """抓取 subreddit feed，并写入旧表和统一表。

    参数：
        req: subreddit 抓取请求。
        db: 异步数据库会话。

    返回：
        dict: 帖子列表与入库统计。
    """
    logger.info(f"[API] 收到抓取版块请求: r/{req.name} (sort={req.sort}, limit={req.limit})")
    try:
        posts = await crawler.fetch_subreddit(req.name, req.sort, req.limit)
        fetched_at = datetime.now(timezone.utc)
        _, created, updated = await save_subreddit_posts(
            db,
            subreddit_name=req.name,
            posts=posts,
            fetched_at=fetched_at,
        )
        await db.commit()

        # 同步创建/更新统一 target 并写入统一模型
        target = await upsert_source_target(
            db,
            source="reddit",
            target_type="subreddit",
            target_key=req.name,
            display_name=req.name,
            monitor_enabled=False,
            fetch_interval=60,
            options={"sort": req.sort, "limit": req.limit},
            fetched_at=fetched_at,
        )
        await db.commit()

        try:
            await fetch_and_ingest_target(
                db,
                source="reddit",
                target_type="subreddit",
                target_key=target.target_key,
                limit=req.limit,
                include_comments=False,
                comment_limit=20,
                options={"sort": req.sort, "limit": req.limit},
            )
        except Exception as ingest_err:
            logger.warning(f"[API] 统一模型写入失败(不影响旧返回): {ingest_err}")

        logger.info(f"[API] 版块抓取成功，共 {len(posts)} 个帖子")
        return {
            "posts": posts,
            "saved": {
                "posts_created": created,
                "posts_updated": updated,
            },
        }
    except httpx.TimeoutException:
        logger.error(f"[API] 请求超时: r/{req.name}")
        raise HTTPException(
            status_code=504,
            detail={
                "error": "TimeoutError",
                "message": "请求 Reddit 超时，请检查网络连接或代理配置",
                "step": "HTTP请求"
            }
        )
    except httpx.ConnectError as e:
        logger.error(f"[API] 连接失败: {repr(e)}")
        raise HTTPException(
            status_code=502,
            detail={
                "error": "ConnectError",
                "message": f"无法连接到 Reddit，请检查网络/代理配置: {repr(e)}",
                "step": "HTTP连接"
            }
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"[API] HTTP 错误: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail={
                "error": "HTTPError",
                "message": f"Reddit 返回错误: {e.response.status_code}",
                "step": "HTTP响应"
            }
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"[API] 未知错误: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": type(e).__name__,
                "message": str(e),
                "step": "未知"
            }
        )
