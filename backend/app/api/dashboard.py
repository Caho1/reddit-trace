from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analysis import Analysis
from app.models.post import Post
from app.models.subreddit import Subreddit
from app.models.tag import Tag

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)

    posts_total = await db.scalar(select(func.count()).select_from(Post))
    subreddits_total = await db.scalar(select(func.count()).select_from(Subreddit))
    subreddits_monitored = await db.scalar(
        select(func.count()).select_from(Subreddit).where(Subreddit.monitor_enabled.is_(True))
    )
    subreddits_fetched = await db.scalar(
        select(func.count()).select_from(Subreddit).where(Subreddit.last_fetched_at.is_not(None))
    )
    tags_total = await db.scalar(select(func.count()).select_from(Tag))
    analyses_valuable_total = await db.scalar(
        select(func.count()).select_from(Analysis).where(Analysis.is_valuable == 1)
    )
    posts_fetched_24h = await db.scalar(
        select(func.count()).select_from(Post).where(Post.fetched_at >= since_24h)
    )

    return {
        "now": now,
        "posts_total": int(posts_total or 0),
        "posts_fetched_24h": int(posts_fetched_24h or 0),
        "subreddits_total": int(subreddits_total or 0),
        "subreddits_monitored": int(subreddits_monitored or 0),
        "subreddits_fetched": int(subreddits_fetched or 0),
        "tags_total": int(tags_total or 0),
        "analyses_valuable_total": int(analyses_valuable_total or 0),
    }

