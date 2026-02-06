from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models.post import Post
from app.models.tag import Tag
from app.schemas.post import PostResponse, PostTagsUpdate
from app.schemas.tag import TagResponse

router = APIRouter()


@router.get("/", response_model=List[PostResponse])
async def list_posts(
    subreddit_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(Post).options(selectinload(Post.tags)).order_by(Post.fetched_at.desc())
    if subreddit_id:
        query = query.where(Post.subreddit_id == subreddit_id)
    if tag_id:
        query = query.where(Post.tags.any(Tag.id == tag_id))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post).options(selectinload(Post.tags)).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("/{post_id}/tags", response_model=List[TagResponse])
async def list_post_tags(post_id: int, db: AsyncSession = Depends(get_db)):
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
