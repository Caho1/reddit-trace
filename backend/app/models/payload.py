from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PostPayload(Base):
    __tablename__ = "post_payloads"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), unique=True, index=True, nullable=False)
    reddit_id = Column(String(20), unique=True, index=True, nullable=False)
    payload = Column(JSONB, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    post = relationship("Post", back_populates="payload")


class CommentPayload(Base):
    __tablename__ = "comment_payloads"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), unique=True, index=True, nullable=False)
    reddit_id = Column(String(20), unique=True, index=True, nullable=False)
    payload = Column(JSONB, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    comment = relationship("Comment", back_populates="payload")

