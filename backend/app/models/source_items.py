from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.source_item_tag_associations import source_item_tags


class SourceItem(Base):
    __tablename__ = "source_items"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("source_targets.id"), nullable=True, index=True)
    source = Column(String(32), nullable=False, index=True)
    external_id = Column(String(64), nullable=False, index=True)
    item_type = Column(String(32), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    title_zh = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    content_zh = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    url = Column(String(1000), nullable=True)
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    target = relationship("SourceTarget", back_populates="items")
    comments = relationship("SourceComment", back_populates="item")
    payload = relationship("SourceItemPayload", back_populates="item", uselist=False, lazy="selectin")
    tags = relationship(
        "Tag",
        secondary=source_item_tags,
        back_populates="source_items",
        lazy="selectin",
        collection_class=set,
    )

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_item_external"),
    )
