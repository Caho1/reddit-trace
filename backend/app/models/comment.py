from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    reddit_id = Column(String(20), unique=True, index=True)
    content = Column(Text)
    content_zh = Column(Text, nullable=True)
    author = Column(String(100))
    score = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    depth = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True))
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="comments")
    analyses = relationship("Analysis", back_populates="comment")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    payload = relationship("CommentPayload", back_populates="comment", uselist=False, lazy="selectin")
