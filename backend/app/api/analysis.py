from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.database import get_db
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisResponse

router = APIRouter()


@router.get("/", response_model=List[AnalysisResponse])
async def list_analyses(
    is_valuable: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(Analysis)
    if is_valuable is not None:
        query = query.where(Analysis.is_valuable == is_valuable)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
