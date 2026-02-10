import json

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SourceComment(Base):
    __tablename__ = "source_comments"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("source_items.id"), nullable=False, index=True)
    source = Column(String(32), nullable=False, index=True)
    external_id = Column(String(64), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_zh = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    score = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("source_comments.id"), nullable=True)
    depth = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    item = relationship("SourceItem", back_populates="comments")
    analyses = relationship("Analysis", back_populates="comment")
    parent = relationship("SourceComment", remote_side=[id], backref="replies")
    analyses = relationship("SourceAnalysis", back_populates="comment")
    payload = relationship(
        "SourceCommentPayload",
        back_populates="comment",
        uselist=False,
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_comment_external"),
    )


class SourceAnalysis(Base):
    __tablename__ = "source_analyses"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("source_comments.id"), nullable=False, index=True)
    pain_points_raw = Column("pain_points", Text, nullable=True)
    user_needs_raw = Column("user_needs", Text, nullable=True)
    opportunities_raw = Column("opportunities", Text, nullable=True)
    model_used = Column(String(50), nullable=True)
    is_valuable = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    comment = relationship("SourceComment", back_populates="analyses")

    @property
    def pain_points(self):
        if not self.pain_points_raw:
            return []
        try:
            return json.loads(self.pain_points_raw)
        except Exception:
            return []

    @pain_points.setter
    def pain_points(self, value):
        self.pain_points_raw = json.dumps(value or [])

    @property
    def user_needs(self):
        if not self.user_needs_raw:
            return []
        try:
            return json.loads(self.user_needs_raw)
        except Exception:
            return []

    @user_needs.setter
    def user_needs(self, value):
        self.user_needs_raw = json.dumps(value or [])

    @property
    def opportunities(self):
        if not self.opportunities_raw:
            return []
        try:
            return json.loads(self.opportunities_raw)
        except Exception:
            return []

    @opportunities.setter
    def opportunities(self, value):
        self.opportunities_raw = json.dumps(value or [])
