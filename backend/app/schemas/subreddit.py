from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SubredditCreate(BaseModel):
    name: str
    description: Optional[str] = None
    monitor_enabled: bool = False
    fetch_interval: int = 60


class SubredditUpdate(BaseModel):
    description: Optional[str] = None
    monitor_enabled: Optional[bool] = None
    fetch_interval: Optional[int] = None


class SubredditResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    monitor_enabled: bool
    fetch_interval: int
    last_fetched_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
