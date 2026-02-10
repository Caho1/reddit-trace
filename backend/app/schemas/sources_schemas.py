from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel

from app.schemas.tags_schemas import TagResponse


class SourceTargetCreate(BaseModel):
    """创建统一目标的请求模型。"""

    source: str
    target_type: str
    target_key: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    monitor_enabled: bool = False
    fetch_interval: int = 60
    options: Dict[str, Any] = {}


class SourceTargetUpdate(BaseModel):
    """更新统一目标的请求模型。"""

    display_name: Optional[str] = None
    description: Optional[str] = None
    monitor_enabled: Optional[bool] = None
    fetch_interval: Optional[int] = None
    options: Optional[Dict[str, Any]] = None


class SourceTargetResponse(BaseModel):
    """统一目标响应模型。"""

    id: int
    source: str
    target_type: str
    target_key: str
    display_name: Optional[str]
    description: Optional[str]
    monitor_enabled: bool
    fetch_interval: int
    options: Dict[str, Any]
    last_fetched_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SourceItemResponse(BaseModel):
    """统一内容响应模型。"""

    id: int
    target_id: Optional[int]
    source: str
    external_id: str
    item_type: str
    title: str
    title_zh: Optional[str]
    content: Optional[str]
    content_zh: Optional[str]
    author: Optional[str]
    url: Optional[str]
    score: int
    num_comments: int
    created_at: datetime
    fetched_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


class SourceItemTagsUpdate(BaseModel):
    """覆盖统一内容标签的请求模型。"""

    tag_ids: List[int] = []


class SourceCommentResponse(BaseModel):
    """统一评论响应模型。"""

    id: int
    item_id: int
    source: str
    external_id: str
    content: str
    content_zh: Optional[str]
    author: Optional[str]
    score: int
    parent_id: Optional[int]
    depth: int
    created_at: datetime
    fetched_at: datetime

    class Config:
        from_attributes = True


class FetchTargetRequest(BaseModel):
    """统一目标抓取请求模型。"""

    target_id: Optional[int] = None
    source: Optional[str] = None
    target_type: Optional[str] = None
    target_key: Optional[str] = None
    limit: int = 30
    include_comments: bool = False
    comment_limit: int = 20
