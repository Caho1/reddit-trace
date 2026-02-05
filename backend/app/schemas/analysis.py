from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AnalysisResponse(BaseModel):
    id: int
    comment_id: int
    pain_points: List[str]
    user_needs: List[str]
    opportunities: List[str]
    model_used: str
    is_valuable: int
    created_at: datetime

    class Config:
        from_attributes = True
