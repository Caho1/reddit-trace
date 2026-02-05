from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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

    class Config:
        from_attributes = True
