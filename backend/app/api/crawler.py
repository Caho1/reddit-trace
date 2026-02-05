from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services import crawler

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
    try:
        result = await crawler.fetch_post(req.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-subreddit")
async def fetch_subreddit(req: FetchSubredditRequest):
    """抓取版块帖子列表"""
    try:
        posts = await crawler.fetch_subreddit(req.name, req.sort, req.limit)
        return {"posts": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
