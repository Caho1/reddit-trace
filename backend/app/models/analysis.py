from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"))
    pain_points = Column(JSONB, default=list)
    user_needs = Column(JSONB, default=list)
    opportunities = Column(JSONB, default=list)
    model_used = Column(String(50))
    is_valuable = Column(Integer, default=0)  # 0=未筛选, 1=有价值, -1=无价值
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    comment = relationship("Comment", back_populates="analyses")
    tags = relationship("AnalysisTag", back_populates="analysis")
