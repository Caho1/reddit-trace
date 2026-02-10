from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models.source_items import SourceItem
from app.models.source_comments import SourceComment
from app.models.source_targets import SourceTarget
from app.models.tags import Tag
from app.schemas.sources_schemas import (
    FetchTargetRequest,
    SourceCommentResponse,
    SourceItemResponse,
    SourceItemTagsUpdate,
    SourceTargetCreate,
    SourceTargetResponse,
    SourceTargetUpdate,
)
from app.schemas.tags_schemas import TagResponse
from app.services.source_fetch_service import fetch_and_ingest_target
from app.services.source_registry_service import source_registry

router = APIRouter()


@router.get("/capabilities")
async def list_source_capabilities():
    """返回各平台适配器能力描述。"""
    return {
        "sources": [adapter.capabilities() for adapter in source_registry.all().values()]
    }


@router.get("/targets", response_model=List[SourceTargetResponse])
async def list_targets(
    source: Optional[str] = None,
    monitor_enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """查询统一目标列表。

    参数：
        source: 可选平台过滤。
        monitor_enabled: 可选监控状态过滤。
        db: 异步数据库会话。

    返回：
        List[SourceTargetResponse]: 过滤后的目标列表。
    """
    query = select(SourceTarget).order_by(SourceTarget.updated_at.desc())
    if source:
        query = query.where(SourceTarget.source == source)
    if monitor_enabled is not None:
        query = query.where(SourceTarget.monitor_enabled.is_(monitor_enabled))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/targets", response_model=SourceTargetResponse)
async def create_target(payload: SourceTargetCreate, db: AsyncSession = Depends(get_db)):
    """创建或更新（幂等）统一目标。

    参数：
        payload: 前端提交的目标参数。
        db: 异步数据库会话。

    返回：
        SourceTargetResponse: 持久化后的目标。
    """
    try:
        adapter = source_registry.get(payload.source)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    source = (payload.source or "").strip().lower()
    target_type = (payload.target_type or "").strip().lower()
    normalized_key = adapter.normalize_target_key(target_type, payload.target_key)

    result = await db.execute(
        select(SourceTarget).where(
            SourceTarget.source == source,
            SourceTarget.target_type == target_type,
            SourceTarget.target_key == normalized_key,
        )
    )
    target = result.scalar_one_or_none()
    if target:
        update_data = payload.model_dump(exclude_unset=True)
        update_data["source"] = source
        update_data["target_type"] = target_type
        update_data["target_key"] = normalized_key
        for key, value in update_data.items():
            setattr(target, key, value)
        await db.commit()
        await db.refresh(target)
        return target

    target = SourceTarget(
        source=source,
        target_type=target_type,
        target_key=normalized_key,
        display_name=payload.display_name or normalized_key,
        description=payload.description,
        monitor_enabled=payload.monitor_enabled,
        fetch_interval=payload.fetch_interval,
        options=payload.options,
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


@router.get("/targets/{target_id}", response_model=SourceTargetResponse)
async def get_target(target_id: int, db: AsyncSession = Depends(get_db)):
    """按 ID 获取统一目标。"""
    result = await db.execute(select(SourceTarget).where(SourceTarget.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


@router.patch("/targets/{target_id}", response_model=SourceTargetResponse)
async def update_target(target_id: int, payload: SourceTargetUpdate, db: AsyncSession = Depends(get_db)):
    """更新统一目标的可变字段。"""
    result = await db.execute(select(SourceTarget).where(SourceTarget.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(target, key, value)

    await db.commit()
    await db.refresh(target)
    return target


@router.delete("/targets/{target_id}")
async def delete_target(target_id: int, db: AsyncSession = Depends(get_db)):
    """删除一个统一目标。"""
    result = await db.execute(select(SourceTarget).where(SourceTarget.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    await db.delete(target)
    await db.commit()
    return {"message": "Deleted"}


@router.post("/fetch")
async def fetch_target(payload: FetchTargetRequest, db: AsyncSession = Depends(get_db)):
    """通过统一抓取链路抓取一个目标。

    参数：
        payload: 抓取请求，可传 ``target_id`` 或三元组参数。
        db: 异步数据库会话。

    返回：
        dict: 目标实体、抓取内容与保存统计。
    """
    target: Optional[SourceTarget] = None
    source = payload.source
    target_type = payload.target_type
    target_key = payload.target_key
    options = {}

    if payload.target_id:
        result = await db.execute(select(SourceTarget).where(SourceTarget.id == payload.target_id))
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        source = target.source
        target_type = target.target_type
        target_key = target.target_key
        options = dict(target.options or {})

    if not source or not target_type or not target_key:
        raise HTTPException(status_code=400, detail="source/target_type/target_key is required")

    try:
        result = await fetch_and_ingest_target(
            db,
            source=source,
            target_type=target_type,
            target_key=target_key,
            limit=payload.limit,
            include_comments=payload.include_comments,
            comment_limit=payload.comment_limit,
            options=options,
        )
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "target": result["target"],
        "items": result["items"],
        "saved": result["saved"],
    }


@router.get("/items", response_model=List[SourceItemResponse])
async def list_items(
    source: Optional[str] = None,
    target_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """查询统一内容列表。"""
    query = select(SourceItem).options(selectinload(SourceItem.tags)).order_by(SourceItem.fetched_at.desc())
    if source:
        query = query.where(SourceItem.source == source)
    if target_id:
        query = query.where(SourceItem.target_id == target_id)
    if tag_id:
        query = query.where(SourceItem.tags.any(Tag.id == tag_id))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/items/{item_id}", response_model=SourceItemResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """按 ID 获取统一内容（含标签）。"""
    result = await db.execute(
        select(SourceItem).options(selectinload(SourceItem.tags)).where(SourceItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/items/{item_id}/tags", response_model=List[TagResponse])
async def list_item_tags(item_id: int, db: AsyncSession = Depends(get_db)):
    """查询统一内容标签列表。"""
    item = await db.get(SourceItem, item_id, options=(selectinload(SourceItem.tags),))
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return list(item.tags)


@router.put("/items/{item_id}/tags", response_model=List[TagResponse])
async def set_item_tags(item_id: int, payload: SourceItemTagsUpdate, db: AsyncSession = Depends(get_db)):
    """覆盖设置统一内容标签。"""
    item = await db.get(SourceItem, item_id, options=(selectinload(SourceItem.tags),))
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if not payload.tag_ids:
        item.tags.clear()
        await db.commit()
        await db.refresh(item)
        return list(item.tags)

    result = await db.execute(select(Tag).where(Tag.id.in_(payload.tag_ids)))
    tags = result.scalars().all()
    found_ids = {tag.id for tag in tags}
    missing_ids = [tag_id for tag_id in payload.tag_ids if tag_id not in found_ids]
    if missing_ids:
        raise HTTPException(status_code=400, detail=f"Tag not found: {missing_ids}")

    item.tags = set(tags)
    await db.commit()
    await db.refresh(item)
    return list(item.tags)


@router.get("/items/{item_id}/comments", response_model=List[SourceCommentResponse])
async def list_item_comments(
    item_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """查询统一内容下的评论列表。"""
    item = await db.get(SourceItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    query = (
        select(SourceComment)
        .where(SourceComment.item_id == item_id)
        .order_by(SourceComment.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()
