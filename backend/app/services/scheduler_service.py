from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from datetime import datetime, timezone
import asyncio

from app.database import AsyncSessionLocal, engine
from app.models.subreddits import Subreddit
from app.models.source_targets import SourceTarget
from app.services.reddit_crawler_service import crawler
from app.services.reddit_ingestion_service import save_subreddit_posts
from app.services.source_fetch_service import fetch_and_ingest_target
from app.logging_config import get_logger

logger = get_logger("reddit_trace.scheduler")


class SchedulerService:
    """定时抓取调度服务。

    同时调度两条链路：
    1) 旧版 subreddit 抓取链路；
    2) 新版统一 source target 抓取链路。
    """

    def __init__(self):
        """初始化 APScheduler 实例。"""
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """启动调度器并注册周期任务。"""
        # 每分钟检查一次需要抓取的版块
        self.scheduler.add_job(
            self.check_and_fetch,
            IntervalTrigger(minutes=1),
            id="check_fetch",
            replace_existing=True
        )
        self.scheduler.start()

    def stop(self):
        """安全停止调度器。"""
        self.scheduler.shutdown()

    async def check_and_fetch(self):
        """扫描监控目标并触发抓取。

        当发生短暂数据库连接异常时会自动重试一次。
        """
        for attempt in range(2):
            try:
                async with AsyncSessionLocal() as db:
                    target_result = await db.execute(
                        select(SourceTarget).where(SourceTarget.monitor_enabled.is_(True))
                    )
                    targets = target_result.scalars().all()

                    for target in targets:
                        if self._should_fetch_target(target):
                            await self.fetch_target(target, db)

                    result = await db.execute(
                        select(Subreddit).where(Subreddit.monitor_enabled.is_(True))
                    )
                    subreddits = result.scalars().all()

                    for sub in subreddits:
                        if self._should_fetch(sub):
                            await self.fetch_subreddit(sub, db)
                return
            except (DBAPIError, ConnectionResetError) as e:
                logger.error(
                    f"[Scheduler] 数据库连接异常（可能是连接被重置/空闲断开），attempt={attempt + 1}/2: {e}",
                    exc_info=True,
                )
                try:
                    await engine.dispose()
                except Exception as dispose_err:
                    logger.warning(
                        f"[Scheduler] dispose engine 失败: {type(dispose_err).__name__}: {dispose_err}",
                        exc_info=True,
                    )
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"[Scheduler] 未知异常: {type(e).__name__}: {e}", exc_info=True)
                return

    def _should_fetch(self, sub: Subreddit) -> bool:
        """判断旧版 subreddit 是否到达抓取时间。

        参数：
            sub: 旧版 ``Subreddit`` 实体。

        返回：
            bool: 当前是否应执行抓取。
        """
        if not sub.last_fetched_at:
            return True
        last = sub.last_fetched_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - last).total_seconds() / 60
        return elapsed >= sub.fetch_interval

    def _should_fetch_target(self, target: SourceTarget) -> bool:
        """判断统一目标是否到达抓取时间。

        参数：
            target: ``SourceTarget`` 实体。

        返回：
            bool: 当前是否应执行抓取。
        """
        if not target.last_fetched_at:
            return True
        last = target.last_fetched_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - last).total_seconds() / 60
        return elapsed >= target.fetch_interval

    async def fetch_target(self, target: SourceTarget, db):
        """抓取一个统一目标并入库。

        参数：
            target: 待抓取目标。
            db: 异步数据库会话。
        """
        try:
            await fetch_and_ingest_target(
                db,
                source=target.source,
                target_type=target.target_type,
                target_key=target.target_key,
                limit=int((target.options or {}).get("limit", 50)),
                include_comments=bool((target.options or {}).get("include_comments", False)),
                comment_limit=int((target.options or {}).get("comment_limit", 20)),
                options=target.options or {},
            )
            logger.info(
                f"[Scheduler] target 抓取完成: source={target.source}, type={target.target_type}, key={target.target_key}"
            )
        except Exception as e:
            await db.rollback()
            logger.error(
                f"[Scheduler] 抓取 target 失败: source={target.source}, key={target.target_key}, err={type(e).__name__}: {e}",
                exc_info=True,
            )

    async def fetch_subreddit(self, sub: Subreddit, db):
        """抓取一个旧版 subreddit 并写入旧表。

        参数：
            sub: 旧版 subreddit 记录。
            db: 异步数据库会话。
        """
        try:
            # 若已同步到新版 source_targets，由统一调度处理，避免重复抓取
            target_exists = await db.scalar(
                select(SourceTarget.id).where(
                    SourceTarget.source == "reddit",
                    SourceTarget.target_type == "subreddit",
                    SourceTarget.target_key == sub.name,
                )
            )
            if target_exists:
                return

            fetched_at = datetime.now(timezone.utc)
            posts = await crawler.fetch_subreddit(sub.name)
            _, created, updated = await save_subreddit_posts(
                db,
                subreddit_name=sub.name,
                posts=posts,
                fetched_at=fetched_at,
            )
            logger.info(
                f"[Scheduler] r/{sub.name} 抓取完成: posts_created={created}, posts_updated={updated}"
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"[Scheduler] 抓取 r/{sub.name} 失败: {type(e).__name__}: {e}", exc_info=True)


scheduler_service = SchedulerService()
