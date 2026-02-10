from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SourceItemPayload(Base):
    __tablename__ = "source_item_payloads"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("source_items.id"), unique=True, index=True, nullable=False)
    source = Column(String(32), nullable=False, index=True)
    external_id = Column(String(64), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    item = relationship("SourceItem", back_populates="payload")


class SourceCommentPayload(Base):
    __tablename__ = "source_comment_payloads"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(
        Integer,
        ForeignKey("source_comments.id"),
        unique=True,
        index=True,
        nullable=False,
    )
    source = Column(String(32), nullable=False, index=True)
    external_id = Column(String(64), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    comment = relationship("SourceComment", back_populates="payload")
