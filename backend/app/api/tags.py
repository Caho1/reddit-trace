from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List

from app.database import get_db
from app.models.tag import Tag, AnalysisTag
from app.models.associations import post_tags
from app.schemas.tag import TagCreate, TagResponse

router = APIRouter()


@router.get("/", response_model=List[TagResponse])
async def list_tags(db: AsyncSession = Depends(get_db)):
    """列出所有标签"""
    result = await db.execute(select(Tag))
    return result.scalars().all()


@router.post("/", response_model=TagResponse)
async def create_tag(data: TagCreate, db: AsyncSession = Depends(get_db)):
    """创建标签"""
    # 检查标签名是否已存在
    result = await db.execute(select(Tag).where(Tag.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tag name already exists")

    tag = Tag(**data.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    """删除标签"""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # 先清理关联关系，避免 FK 冲突
    await db.execute(delete(AnalysisTag).where(AnalysisTag.tag_id == tag_id))
    await db.execute(delete(post_tags).where(post_tags.c.tag_id == tag_id))

    await db.delete(tag)
    await db.commit()
    return {"message": "Deleted"}
