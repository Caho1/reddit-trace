from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AnalysisResponse(BaseModel):
    """分析结果响应模型。"""

    id: int
    comment_id: int
    source: Optional[str] = None
    item_id: Optional[int] = None
    pain_points: List[str]
    user_needs: List[str]
    opportunities: List[str]
    model_used: str
    is_valuable: int
    created_at: datetime

    class Config:
        from_attributes = True
