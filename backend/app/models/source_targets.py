from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SourceTarget(Base):
    __tablename__ = "source_targets"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(32), nullable=False, index=True)
    target_type = Column(String(32), nullable=False, index=True)
    target_key = Column(String(200), nullable=False, index=True)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    monitor_enabled = Column(Boolean, default=False)
    fetch_interval = Column(Integer, default=60)  # 分钟
    options = Column(JSONB, default=dict)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items = relationship("SourceItem", back_populates="target")

    __table_args__ = (
        UniqueConstraint("source", "target_type", "target_key", name="uq_source_target"),
    )

