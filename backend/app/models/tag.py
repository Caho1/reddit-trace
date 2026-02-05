from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    color = Column(String(20), default="#1890ff")
    description = Column(Text, nullable=True)


class AnalysisTag(Base):
    __tablename__ = "analysis_tags"

    analysis_id = Column(Integer, ForeignKey("analyses.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)

    analysis = relationship("Analysis", back_populates="tags")
    tag = relationship("Tag")
