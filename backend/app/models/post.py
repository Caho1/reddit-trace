from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    subreddit_id = Column(Integer, ForeignKey("subreddits.id"))
    reddit_id = Column(String(20), unique=True, index=True)
    title = Column(String(500))
    title_zh = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    content_zh = Column(Text, nullable=True)
    author = Column(String(100))
    url = Column(String(500))
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True))
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    subreddit = relationship("Subreddit", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
