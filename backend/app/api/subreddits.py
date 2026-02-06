from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.subreddit import Subreddit
from app.schemas.subreddit import SubredditCreate, SubredditUpdate, SubredditResponse
from app.services.ingest import normalize_subreddit_name

router = APIRouter()


@router.get("/", response_model=List[SubredditResponse])
async def list_subreddits(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subreddit))
    return result.scalars().all()


@router.post("/", response_model=SubredditResponse)
async def create_subreddit(data: SubredditCreate, db: AsyncSession = Depends(get_db)):
    normalized_name = normalize_subreddit_name(data.name)

    result = await db.execute(select(Subreddit).where(Subreddit.name == normalized_name))
    subreddit = result.scalar_one_or_none()

    if subreddit:
        payload = data.model_dump(exclude_unset=True)
        payload.pop("name", None)
        for key, value in payload.items():
            setattr(subreddit, key, value)

        await db.commit()
        await db.refresh(subreddit)
        return subreddit

    payload = data.model_dump()
    payload["name"] = normalized_name
    subreddit = Subreddit(**payload)
    db.add(subreddit)
    await db.commit()
    await db.refresh(subreddit)
    return subreddit


@router.get("/{subreddit_id}", response_model=SubredditResponse)
async def get_subreddit(subreddit_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subreddit).where(Subreddit.id == subreddit_id))
    subreddit = result.scalar_one_or_none()
    if not subreddit:
        raise HTTPException(status_code=404, detail="Subreddit not found")
    return subreddit


@router.patch("/{subreddit_id}", response_model=SubredditResponse)
async def update_subreddit(
    subreddit_id: int, data: SubredditUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Subreddit).where(Subreddit.id == subreddit_id))
    subreddit = result.scalar_one_or_none()
    if not subreddit:
        raise HTTPException(status_code=404, detail="Subreddit not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(subreddit, key, value)

    await db.commit()
    await db.refresh(subreddit)
    return subreddit


@router.delete("/{subreddit_id}")
async def delete_subreddit(subreddit_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subreddit).where(Subreddit.id == subreddit_id))
    subreddit = result.scalar_one_or_none()
    if not subreddit:
        raise HTTPException(status_code=404, detail="Subreddit not found")

    await db.delete(subreddit)
    await db.commit()
    return {"message": "Deleted"}
