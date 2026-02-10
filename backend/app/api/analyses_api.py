from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models.analyses import Analysis
from app.models.source_comments import SourceAnalysis
from app.models.source_comments import SourceComment
from app.schemas.analyses_schemas import AnalysisResponse

router = APIRouter()


@router.get("/", response_model=List[AnalysisResponse])
async def list_analyses(
    is_valuable: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """查询旧版分析结果列表（支持价值过滤）。"""
    query = select(Analysis).options(selectinload(Analysis.comment))
    if is_valuable is not None:
        query = query.where(Analysis.is_valuable == is_valuable)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()
    return [
        AnalysisResponse(
            id=row.id,
            comment_id=row.comment_id,
            source=getattr(row.comment, "source", None),
            item_id=getattr(row.comment, "item_id", None),
            pain_points=row.pain_points,
            user_needs=row.user_needs,
            opportunities=row.opportunities,
            model_used=row.model_used,
            is_valuable=row.is_valuable,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/sources", response_model=List[AnalysisResponse])
async def list_source_analyses(
    source: Optional[str] = None,
    is_valuable: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """查询统一来源评论分析结果列表。"""
    query = select(SourceAnalysis).options(selectinload(SourceAnalysis.comment))
    if is_valuable is not None:
        query = query.where(SourceAnalysis.is_valuable == is_valuable)
    if source:
        query = query.join(SourceAnalysis.comment).where(SourceComment.source == source)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()
    return [
        AnalysisResponse(
            id=row.id,
            comment_id=row.comment_id,
            source=getattr(row.comment, "source", None),
            item_id=getattr(row.comment, "item_id", None),
            pain_points=row.pain_points,
            user_needs=row.user_needs,
            opportunities=row.opportunities,
            model_used=row.model_used or "",
            is_valuable=row.is_valuable,
            created_at=row.created_at,
        )
        for row in rows
    ]
