from __future__ import annotations
"""统一来源入库服务。

负责将多平台抓取结果写入 ``source_*`` 系列表，包含：
- 目标（source_targets）
- 内容（source_items）
- 评论（source_comments）
- 原始载荷（source_item_payloads/source_comment_payloads）
- 标签关联（source_item_tags）
"""

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_item_tag_associations import source_item_tags
from app.models.source_comments import SourceComment
from app.models.source_items import SourceItem
from app.models.source_payloads import SourceCommentPayload, SourceItemPayload
from app.models.source_targets import SourceTarget
from app.models.tags import Tag


def normalize_target_key(target_key: str) -> str:
    """标准化目标键。

    参数：
        target_key: 来自 API/UI 的原始目标键。

    返回：
        str: 去除冗余前缀后的目标键。
    """
    key = (target_key or "").strip()
    if key.lower().startswith("r/"):
        key = key[2:]
    return key


def ensure_utc(dt: Optional[datetime]) -> datetime:
    """将时间值转换为 UTC 时区感知时间。

    参数：
        dt: 输入时间，可为 ``None`` 或无时区时间。

    返回：
        datetime: UTC 时区感知时间。
    """
    if not dt:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_source(value: str) -> str:
    """标准化平台标识字符串。

    参数：
        value: 原始平台标识。

    返回：
        str: 小写平台键。
    """
    return (value or "").strip().lower()


async def upsert_source_target(
    db: AsyncSession,
    *,
    source: str,
    target_type: str,
    target_key: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    monitor_enabled: Optional[bool] = None,
    fetch_interval: Optional[int] = None,
    options: Optional[Dict[str, Any]] = None,
    fetched_at: Optional[datetime] = None,
) -> SourceTarget:
    """创建或更新统一目标记录。

    参数：
        db: 异步数据库会话。
        source: 平台键。
        target_type: 目标类型。
        target_key: 目标唯一键。
        display_name: 可选展示名称。
        description: 可选描述。
        monitor_enabled: 可选监控开关。
        fetch_interval: 可选抓取间隔（分钟）。
        options: 可选平台参数。
        fetched_at: 可选最近抓取时间。

    返回：
        SourceTarget: 持久化后的目标实体。

    异常：
        ValueError: 必要标识字段为空时抛出。
    """
    source = normalize_source(source)
    target_type = (target_type or "").strip().lower()
    target_key = normalize_target_key(target_key)
    if not source or not target_type or not target_key:
        raise ValueError("source/target_type/target_key is required")

    result = await db.execute(
        select(SourceTarget).where(
            SourceTarget.source == source,
            SourceTarget.target_type == target_type,
            SourceTarget.target_key == target_key,
        )
    )
    entity = result.scalar_one_or_none()
    if not entity:
        entity = SourceTarget(
            source=source,
            target_type=target_type,
            target_key=target_key,
            display_name=display_name or target_key,
            description=description,
            monitor_enabled=bool(monitor_enabled) if monitor_enabled is not None else False,
            fetch_interval=int(fetch_interval) if fetch_interval is not None else 60,
            options=options or {},
        )
        db.add(entity)
        await db.flush()
    else:
        if display_name is not None:
            entity.display_name = display_name
        if description is not None:
            entity.description = description
        entity.monitor_enabled = monitor_enabled if monitor_enabled is not None else entity.monitor_enabled
        entity.fetch_interval = fetch_interval if fetch_interval is not None else entity.fetch_interval
        if options is not None:
            entity.options = options

    if fetched_at:
        entity.last_fetched_at = ensure_utc(fetched_at)

    return entity


async def _get_or_create_tags(db: AsyncSession, names: Iterable[str]) -> Dict[str, Tag]:
    """读取已有标签并补齐缺失标签。

    参数：
        db: 异步数据库会话。
        names: 候选标签名称集合。

    返回：
        Dict[str, Tag]: 标签名到标签实体的映射。
    """
    normalized = {str(name).strip() for name in names if str(name).strip()}
    if not normalized:
        return {}

    result = await db.execute(select(Tag).where(Tag.name.in_(normalized)))
    found = {tag.name: tag for tag in result.scalars().all()}

    for name in sorted(normalized):
        if name in found:
            continue
        tag = Tag(name=name)
        db.add(tag)
        found[name] = tag

    await db.flush()
    return found


async def save_source_items(
    db: AsyncSession,
    *,
    source: str,
    target: Optional[SourceTarget],
    items: List[Dict[str, Any]],
    fetched_at: Optional[datetime] = None,
) -> Tuple[int, int]:
    """批量 Upsert 统一内容、payload 与标签关联。

    参数：
        db: 异步数据库会话。
        source: 平台键。
        target: 关联目标（可选）。
        items: 规范化后的内容字典列表。
        fetched_at: 抓取时间。

    返回：
        Tuple[int, int]: ``(新增数量, 更新数量)``。
    """
    source = normalize_source(source)
    fetched_at = ensure_utc(fetched_at)

    external_ids = [str(item.get("external_id") or "").strip() for item in items if item.get("external_id")]
    existing: Dict[str, SourceItem] = {}
    if external_ids:
        result = await db.execute(
            select(SourceItem).where(
                SourceItem.source == source,
                SourceItem.external_id.in_(external_ids),
            )
        )
        existing = {row.external_id: row for row in result.scalars().all()}

    tag_map = await _get_or_create_tags(
        db,
        names=[tag for item in items for tag in (item.get("tags") or [])],
    )

    created = 0
    updated = 0
    for raw in items:
        external_id = str(raw.get("external_id") or "").strip()
        if not external_id:
            continue

        row = existing.get(external_id)
        created_at = ensure_utc(raw.get("created_at"))

        payload = {
            "target_id": target.id if target else None,
            "source": source,
            "external_id": external_id,
            "item_type": str(raw.get("item_type") or "post"),
            "title": str(raw.get("title") or ""),
            "content": raw.get("content"),
            "author": raw.get("author"),
            "url": raw.get("url"),
            "score": int(raw.get("score") or 0),
            "num_comments": int(raw.get("num_comments") or 0),
            "created_at": created_at,
            "fetched_at": fetched_at,
        }

        if row:
            updated += 1
            for key, value in payload.items():
                setattr(row, key, value)
        else:
            created += 1
            row = SourceItem(**payload)
            db.add(row)
            existing[external_id] = row

    await db.flush()

    payload_map: Dict[str, SourceItemPayload] = {}
    if external_ids:
        result = await db.execute(
            select(SourceItemPayload).where(
                SourceItemPayload.source == source,
                SourceItemPayload.external_id.in_(external_ids),
            )
        )
        payload_rows = result.scalars().all()
        payload_map = {f"{row.source}:{row.external_id}": row for row in payload_rows}

    for raw in items:
        external_id = str(raw.get("external_id") or "").strip()
        if not external_id:
            continue
        item = existing.get(external_id)
        if not item:
            continue

        payload = payload_map.get(f"{source}:{external_id}")
        if payload:
            payload.item_id = item.id
            payload.payload = jsonable_encoder(raw.get("payload") or raw)
            payload.fetched_at = fetched_at
        else:
            db.add(
                SourceItemPayload(
                    item_id=item.id,
                    source=source,
                    external_id=external_id,
                    payload=jsonable_encoder(raw.get("payload") or raw),
                    fetched_at=fetched_at,
                )
            )

    tag_links: List[Dict[str, int]] = []
    for raw in items:
        external_id = str(raw.get("external_id") or "").strip()
        if not external_id:
            continue
        item = existing.get(external_id)
        if not item:
            continue

        for raw_tag in (raw.get("tags") or []):
            name = str(raw_tag).strip()
            if not name:
                continue
            tag = tag_map.get(name)
            if tag and item.id and tag.id:
                tag_links.append({"source_item_id": item.id, "tag_id": tag.id})

    if tag_links:
        await db.execute(pg_insert(source_item_tags).values(tag_links).on_conflict_do_nothing())

    await db.flush()
    return created, updated


async def save_source_comments(
    db: AsyncSession,
    *,
    source: str,
    item: SourceItem,
    comments: List[Dict[str, Any]],
    fetched_at: Optional[datetime] = None,
) -> Tuple[int, int]:
    """批量 Upsert 统一评论与评论 payload。

    参数：
        db: 异步数据库会话。
        source: 平台键。
        item: 父级内容实体。
        comments: 规范化后的评论字典列表。
        fetched_at: 抓取时间。

    返回：
        Tuple[int, int]: ``(新增数量, 更新数量)``。
    """
    source = normalize_source(source)
    fetched_at = ensure_utc(fetched_at)

    external_ids = [str(comment.get("external_id") or "").strip() for comment in comments if comment.get("external_id")]
    existing: Dict[str, SourceComment] = {}
    if external_ids:
        result = await db.execute(
            select(SourceComment).where(
                SourceComment.source == source,
                SourceComment.external_id.in_(external_ids),
            )
        )
        existing = {row.external_id: row for row in result.scalars().all()}

    created = 0
    updated = 0
    for raw in comments:
        external_id = str(raw.get("external_id") or "").strip()
        if not external_id:
            continue

        row = existing.get(external_id)
        payload = {
            "item_id": item.id,
            "source": source,
            "external_id": external_id,
            "content": str(raw.get("content") or ""),
            "author": raw.get("author"),
            "score": int(raw.get("score") or 0),
            "depth": int(raw.get("depth") or 0),
            "created_at": ensure_utc(raw.get("created_at")),
            "fetched_at": fetched_at,
        }

        if row:
            updated += 1
            for key, value in payload.items():
                setattr(row, key, value)
        else:
            created += 1
            row = SourceComment(**payload)
            db.add(row)
            existing[external_id] = row

    await db.flush()

    for raw in comments:
        external_id = str(raw.get("external_id") or "").strip()
        if not external_id:
            continue
        row = existing.get(external_id)
        if not row:
            continue

        parent_external_id = raw.get("parent_external_id")
        parent_id: Optional[int] = None
        if parent_external_id:
            parent = existing.get(str(parent_external_id))
            if parent:
                parent_id = parent.id
        row.parent_id = parent_id

    await db.flush()

    payload_map: Dict[str, SourceCommentPayload] = {}
    if external_ids:
        result = await db.execute(
            select(SourceCommentPayload).where(
                SourceCommentPayload.source == source,
                SourceCommentPayload.external_id.in_(external_ids),
            )
        )
        payload_rows = result.scalars().all()
        payload_map = {f"{row.source}:{row.external_id}": row for row in payload_rows}

    for raw in comments:
        external_id = str(raw.get("external_id") or "").strip()
        if not external_id:
            continue
        row = existing.get(external_id)
        if not row:
            continue

        payload = payload_map.get(f"{source}:{external_id}")
        if payload:
            payload.comment_id = row.id
            payload.payload = jsonable_encoder(raw.get("payload") or raw)
            payload.fetched_at = fetched_at
        else:
            db.add(
                SourceCommentPayload(
                    comment_id=row.id,
                    source=source,
                    external_id=external_id,
                    payload=jsonable_encoder(raw.get("payload") or raw),
                    fetched_at=fetched_at,
                )
            )

    await db.flush()
    return created, updated
