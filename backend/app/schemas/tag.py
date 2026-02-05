from pydantic import BaseModel
from typing import Optional


class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#1890ff"
    description: Optional[str] = None


class TagResponse(BaseModel):
    id: int
    name: str
    color: str
    description: Optional[str]

    class Config:
        from_attributes = True
