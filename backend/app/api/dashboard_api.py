from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analyses import Analysis
from app.models.source_comments import SourceAnalysis
from app.models.posts import Post
from app.models.subreddits import Subreddit
from app.models.source_items import SourceItem
from app.models.source_targets import SourceTarget
from app.models.tags import Tag

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """返回仪表盘核心统计（旧版 + 统一模型）。"""
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)

    posts_total = await db.scalar(select(func.count()).select_from(Post))
    source_items_total = await db.scalar(select(func.count()).select_from(SourceItem))
    subreddits_total = await db.scalar(select(func.count()).select_from(Subreddit))
    targets_total = await db.scalar(select(func.count()).select_from(SourceTarget))
    targets_monitored = await db.scalar(
        select(func.count()).select_from(SourceTarget).where(SourceTarget.monitor_enabled.is_(True))
    )
    targets_fetched = await db.scalar(
        select(func.count()).select_from(SourceTarget).where(SourceTarget.last_fetched_at.is_not(None))
    )
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
    source_analyses_valuable_total = await db.scalar(
        select(func.count()).select_from(SourceAnalysis).where(SourceAnalysis.is_valuable == 1)
    )
    posts_fetched_24h = await db.scalar(
        select(func.count()).select_from(Post).where(Post.fetched_at >= since_24h)
    )
    source_items_fetched_24h = await db.scalar(
        select(func.count()).select_from(SourceItem).where(SourceItem.fetched_at >= since_24h)
    )

    return {
        "now": now,
        "posts_total": int(posts_total or 0),
        "source_items_total": int(source_items_total or 0),
        "posts_fetched_24h": int(posts_fetched_24h or 0),
        "source_items_fetched_24h": int(source_items_fetched_24h or 0),
        "subreddits_total": int(subreddits_total or 0),
        "targets_total": int(targets_total or 0),
        "targets_monitored": int(targets_monitored or 0),
        "targets_fetched": int(targets_fetched or 0),
        "subreddits_monitored": int(subreddits_monitored or 0),
        "subreddits_fetched": int(subreddits_fetched or 0),
        "tags_total": int(tags_total or 0),
        "analyses_valuable_total": int(analyses_valuable_total or 0),
        "source_analyses_valuable_total": int(source_analyses_valuable_total or 0),
    }

