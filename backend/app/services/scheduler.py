from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from datetime import datetime

from app.database import AsyncSessionLocal
from app.models.subreddit import Subreddit
from app.services.crawler import crawler
from app.services.analyzer import analyzer


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
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Subreddit).where(Subreddit.monitor_enabled == True)
            )
            subreddits = result.scalars().all()

            for sub in subreddits:
                if self._should_fetch(sub):
                    await self.fetch_subreddit(sub, db)

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
            print(f"Error fetching {sub.name}: {e}")


scheduler_service = SchedulerService()
