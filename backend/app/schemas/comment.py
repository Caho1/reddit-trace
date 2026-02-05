from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CommentResponse(BaseModel):
    id: int
    post_id: int
    reddit_id: str
    content: str
    content_zh: Optional[str]
    author: str
    score: int
    parent_id: Optional[int]
    depth: int
    created_at: datetime
    fetched_at: datetime

    class Config:
        from_attributes = True
