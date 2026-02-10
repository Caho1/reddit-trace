"""帖子查询与标签操作 API。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.posts import Post
from app.models.source_items import SourceItem
from app.models.tags import Tag
from app.schemas.posts_schemas import PostResponse, PostTagsUpdate
from app.schemas.tags_schemas import TagResponse

router = APIRouter()


def _to_post_response_from_source_item(item: SourceItem) -> PostResponse:
    """将统一内容模型转换为兼容的帖子响应。

    Args:
        item: 统一内容表中的单条记录。

    Returns:
        PostResponse: 前端兼容的帖子数据结构。
    """
    return PostResponse(
        id=item.id,
        subreddit_id=item.target_id or 0,
        reddit_id=item.external_id,
        title=item.title,
        title_zh=item.title_zh,
        content=item.content,
        content_zh=item.content_zh,
        author=item.author or "unknown",
        url=item.url or "",
        score=item.score,
        num_comments=item.num_comments,
        created_at=item.created_at,
        fetched_at=item.fetched_at,
        tags=list(item.tags),
        source=item.source,
    )


@router.get("", response_model=List[PostResponse])
@router.get("/", response_model=List[PostResponse])
async def list_posts(
    source: Optional[str] = None,
    target_id: Optional[int] = None,
    subreddit_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """查询帖子列表（默认走统一多源模型）。

    Args:
        source: 可选平台过滤，如 ``reddit`` / ``hackernews``。
        target_id: 可选目标 ID（统一模型）。
        subreddit_id: 旧版 subreddit ID，仅用于 legacy 兼容。
        tag_id: 可选标签过滤。
        skip: 分页偏移。
        limit: 分页大小。
        db: 异步数据库会话。

    Returns:
        List[PostResponse]: 统一格式的帖子列表。
    """
    # 默认返回统一模型，确保多源场景下不丢 HN 等平台内容。
    # 当传入 legacy 的 subreddit_id（且目标未指定）时，回退旧表查询以兼容旧筛选行为。
    use_legacy_posts = subreddit_id is not None and target_id is None and source in (None, "reddit")
    use_unified_source_items = not use_legacy_posts

    if use_unified_source_items:
        query = (
            select(SourceItem)
            .options(selectinload(SourceItem.tags))
            .order_by(SourceItem.fetched_at.desc())
        )
        if source:
            query = query.where(SourceItem.source == source)
        if target_id:
            query = query.where(SourceItem.target_id == target_id)
        if tag_id:
            query = query.where(SourceItem.tags.any(Tag.id == tag_id))
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.scalars().all()
        return [_to_post_response_from_source_item(row) for row in rows]

    query = select(Post).options(selectinload(Post.tags)).order_by(Post.fetched_at.desc())
    if subreddit_id:
        query = query.where(Post.subreddit_id == subreddit_id)
    if tag_id:
        query = query.where(Post.tags.any(Tag.id == tag_id))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()
    return [
        PostResponse(
            id=row.id,
            subreddit_id=row.subreddit_id,
            reddit_id=row.reddit_id,
            title=row.title,
            title_zh=row.title_zh,
            content=row.content,
            content_zh=row.content_zh,
            author=row.author,
            url=row.url,
            score=row.score,
            num_comments=row.num_comments,
            created_at=row.created_at,
            fetched_at=row.fetched_at,
            tags=list(row.tags),
            source="reddit",
        )
        for row in rows
    ]


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """按 ID 获取单条旧版帖子。"""
    result = await db.execute(
        select(Post).options(selectinload(Post.tags)).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("/{post_id}/tags", response_model=List[TagResponse])
async def list_post_tags(post_id: int, db: AsyncSession = Depends(get_db)):
    """查询单条旧版帖子的标签。"""
    post = await db.get(Post, post_id, options=(selectinload(Post.tags),))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return list(post.tags)


@router.put("/{post_id}/tags", response_model=List[TagResponse])
async def set_post_tags(
    post_id: int,
    payload: PostTagsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """覆盖设置单条旧版帖子的标签绑定。"""
    post = await db.get(Post, post_id, options=(selectinload(Post.tags),))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not payload.tag_ids:
        post.tags.clear()
        await db.commit()
        await db.refresh(post)
        return list(post.tags)

    result = await db.execute(select(Tag).where(Tag.id.in_(payload.tag_ids)))
    tags = result.scalars().all()

    found_ids = {t.id for t in tags}
    missing = [tid for tid in payload.tag_ids if tid not in found_ids]
    if missing:
        raise HTTPException(status_code=400, detail=f"Tag not found: {missing}")

    post.tags = set(tags)
    await db.commit()
    await db.refresh(post)
    return list(post.tags)
