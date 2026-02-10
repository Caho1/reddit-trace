from sqlalchemy import Table, Column, Integer, ForeignKey

from app.database import Base


source_item_tags = Table(
    "source_item_tags",
    Base.metadata,
    Column("source_item_id", Integer, ForeignKey("source_items.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

