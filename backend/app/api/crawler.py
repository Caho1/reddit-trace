from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import httpx

from app.database import get_db
from app.services import crawler
from app.logging_config import get_logger

logger = get_logger("reddit_trace.api.crawler")

router = APIRouter()


class FetchRequest(BaseModel):
    url: str


class FetchSubredditRequest(BaseModel):
    name: str
    sort: str = "hot"
    limit: int = 25


@router.post("/fetch-post")
async def fetch_post(req: FetchRequest, db: AsyncSession = Depends(get_db)):
    """抓取单个帖子及其评论"""
    logger.info(f"[API] 收到抓取帖子请求: {req.url}")
    try:
        result = await crawler.fetch_post(req.url)
        logger.info(f"[API] 帖子抓取成功")
        return result
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
        logger.error(f"[API] 未知错误: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": type(e).__name__,
                "message": str(e),
                "step": "未知"
            }
        )


@router.post("/fetch-subreddit")
async def fetch_subreddit(req: FetchSubredditRequest):
    """抓取版块帖子列表"""
    logger.info(f"[API] 收到抓取版块请求: r/{req.name} (sort={req.sort}, limit={req.limit})")
    try:
        posts = await crawler.fetch_subreddit(req.name, req.sort, req.limit)
        logger.info(f"[API] 版块抓取成功，共 {len(posts)} 个帖子")
        return {"posts": posts}
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
        logger.error(f"[API] 未知错误: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": type(e).__name__,
                "message": str(e),
                "step": "未知"
            }
        )
