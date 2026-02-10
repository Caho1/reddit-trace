from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_items import SourceItem
from app.models.source_targets import SourceTarget
from app.services.source_ingestion_service import (
    save_source_comments,
    save_source_items,
    upsert_source_target,
)
from app.services.source_registry_service import source_registry


async def fetch_and_ingest_target(
    db: AsyncSession,
    *,
    source: str,
    target_type: str,
    target_key: str,
    limit: int,
    include_comments: bool,
    comment_limit: int,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """抓取并入库一个统一目标。

    参数：
        db: 异步数据库会话。
        source: 平台标识（如 ``reddit`` / ``hackernews``）。
        target_type: 目标类型（由适配器能力定义）。
        target_key: 原始目标键。
        limit: 抓取条数上限。
        include_comments: 是否抓取评论。
        comment_limit: 每条内容最大评论数。
        options: 平台特定参数（sort/feed 等）。

    返回：
        Dict[str, Any]: 目标实体、原始内容与保存统计。
    """
    source = (source or "").strip().lower()
    adapter = source_registry.get(source)
    normalized_key = adapter.normalize_target_key(target_type, target_key)
    fetched_at = datetime.now(timezone.utc)

    target = await upsert_source_target(
        db,
        source=source,
        target_type=target_type,
        target_key=normalized_key,
        fetched_at=fetched_at,
        options=options or {},
    )

    raw_items = await adapter.fetch_target_items(
        target_type=target_type,
        target_key=normalized_key,
        limit=limit,
        options=options or {},
    )

    items_created, items_updated = await save_source_items(
        db,
        source=source,
        target=target,
        items=raw_items,
        fetched_at=fetched_at,
    )

    comments_created_total = 0
    comments_updated_total = 0

    if include_comments:
        external_ids = [str(item.get("external_id") or "").strip() for item in raw_items if item.get("external_id")]
        if external_ids:
            result = await db.execute(
                select(SourceItem).where(
                    SourceItem.source == source,
                    SourceItem.external_id.in_(external_ids),
                )
            )
            db_items = {row.external_id: row for row in result.scalars().all()}

            for raw in raw_items:
                external_id = str(raw.get("external_id") or "").strip()
                db_item = db_items.get(external_id)
                if not db_item:
                    continue
                raw_comments = raw.get("comments")
                if raw_comments is None:
                    raw_comments = await adapter.fetch_item_comments(
                        item_external_id=external_id,
                        item_url=raw.get("url"),
                        limit=comment_limit,
                        options=options or {},
                    )
                created, updated = await save_source_comments(
                    db,
                    source=source,
                    item=db_item,
                    comments=raw_comments[: max(1, int(comment_limit))],
                    fetched_at=fetched_at,
                )
                comments_created_total += created
                comments_updated_total += updated

    target.last_fetched_at = fetched_at
    await db.commit()

    return {
        "target": target,
        "items": raw_items,
        "saved": {
            "items_created": items_created,
            "items_updated": items_updated,
            "comments_created": comments_created_total,
            "comments_updated": comments_updated_total,
        },
    }
