from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from app.schemas.tags_schemas import TagResponse


class PostTagsUpdate(BaseModel):
    """用于覆盖帖子标签的请求模型。

    Attributes:
        tag_ids: 目标标签 ID 列表。
    """

    tag_ids: List[int] = []


class PostResponse(BaseModel):
    """面向前端兼容的统一帖子响应模型。"""

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
    source: str = "reddit"

    class Config:
        from_attributes = True
