from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from datetime import datetime
import asyncio

from app.database import AsyncSessionLocal
from app.models.subreddit import Subreddit
from app.services.crawler import crawler
from app.services.analyzer import analyzer
from app.logging_config import get_logger

logger = get_logger("reddit_trace.scheduler")


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        # 每分钟检查一次需要抓取的版块
        self.scheduler.add_job(
            self.check_and_fetch,
            IntervalTrigger(minutes=1),
            id="check_fetch",
            replace_existing=True
        )
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()

    async def check_and_fetch(self):
        """检查并执行需要抓取的任务"""
        for attempt in range(2):
            try:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(Subreddit).where(Subreddit.monitor_enabled.is_(True))
                    )
                    subreddits = result.scalars().all()

                    for sub in subreddits:
                        if self._should_fetch(sub):
                            await self.fetch_subreddit(sub, db)
                return
            except DBAPIError as e:
                logger.error(
                    f"[Scheduler] 数据库连接异常（可能是连接被重置/空闲断开），attempt={attempt + 1}/2: {e}",
                    exc_info=True,
                )
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"[Scheduler] 未知异常: {type(e).__name__}: {e}", exc_info=True)
                return

    def _should_fetch(self, sub: Subreddit) -> bool:
        if not sub.last_fetched_at:
            return True
        elapsed = (datetime.utcnow() - sub.last_fetched_at).total_seconds() / 60
        return elapsed >= sub.fetch_interval

    async def fetch_subreddit(self, sub: Subreddit, db):
        """抓取版块数据"""
        try:
            posts = await crawler.fetch_subreddit(sub.name)
            # TODO: 保存帖子和评论到数据库
            sub.last_fetched_at = datetime.utcnow()
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"[Scheduler] 抓取 r/{sub.name} 失败: {type(e).__name__}: {e}", exc_info=True)


scheduler_service = SchedulerService()
