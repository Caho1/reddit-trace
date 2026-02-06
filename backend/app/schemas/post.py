from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from app.schemas.tag import TagResponse


class PostTagsUpdate(BaseModel):
    tag_ids: List[int] = []


class PostResponse(BaseModel):
    id: int
    subreddit_id: int
    reddit_id: str
    title: str
    title_zh: Optional[str]
    content: Optional[str]
    content_zh: Optional[str]
    author: str
    url: str
    score: int
    num_comments: int
    created_at: datetime
    fetched_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True
