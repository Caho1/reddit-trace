"""add_source_platform_schema

Revision ID: 949220c7deae
Revises: 
Create Date: 2026-02-10 16:41:01.585796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '949220c7deae'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "source_targets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_key", sa.String(length=200), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("monitor_enabled", sa.Boolean(), nullable=True),
        sa.Column("fetch_interval", sa.Integer(), nullable=True),
        sa.Column(
            "options",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "target_type", "target_key", name="uq_source_target"),
    )
    op.create_index("ix_source_targets_source", "source_targets", ["source"], unique=False)
    op.create_index("ix_source_targets_target_type", "source_targets", ["target_type"], unique=False)
    op.create_index("ix_source_targets_target_key", "source_targets", ["target_key"], unique=False)

    op.create_table(
        "source_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("title_zh", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("content_zh", sa.Text(), nullable=True),
        sa.Column("author", sa.String(length=100), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("num_comments", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["target_id"], ["source_targets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id", name="uq_source_item_external"),
    )
    op.create_index("ix_source_items_target_id", "source_items", ["target_id"], unique=False)
    op.create_index("ix_source_items_source", "source_items", ["source"], unique=False)
    op.create_index("ix_source_items_external_id", "source_items", ["external_id"], unique=False)
    op.create_index("ix_source_items_item_type", "source_items", ["item_type"], unique=False)

    op.create_table(
        "source_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_zh", sa.Text(), nullable=True),
        sa.Column("author", sa.String(length=100), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["source_items.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["source_comments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id", name="uq_source_comment_external"),
    )
    op.create_index("ix_source_comments_item_id", "source_comments", ["item_id"], unique=False)
    op.create_index("ix_source_comments_source", "source_comments", ["source"], unique=False)
    op.create_index("ix_source_comments_external_id", "source_comments", ["external_id"], unique=False)
    op.create_index("ix_source_comments_parent_id", "source_comments", ["parent_id"], unique=False)

    op.create_table(
        "source_item_payloads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["source_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id"),
    )
    op.create_index("ix_source_item_payloads_source", "source_item_payloads", ["source"], unique=False)
    op.create_index("ix_source_item_payloads_external_id", "source_item_payloads", ["external_id"], unique=False)

    op.create_table(
        "source_comment_payloads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["comment_id"], ["source_comments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("comment_id"),
    )
    op.create_index("ix_source_comment_payloads_source", "source_comment_payloads", ["source"], unique=False)
    op.create_index("ix_source_comment_payloads_external_id", "source_comment_payloads", ["external_id"], unique=False)

    op.create_table(
        "source_item_tags",
        sa.Column("source_item_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["source_item_id"], ["source_items.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.PrimaryKeyConstraint("source_item_id", "tag_id"),
    )

    op.create_table(
        "source_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column("pain_points", sa.Text(), nullable=True),
        sa.Column("user_needs", sa.Text(), nullable=True),
        sa.Column("opportunities", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(length=50), nullable=True),
        sa.Column("is_valuable", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["comment_id"], ["source_comments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_source_analyses_comment_id", "source_analyses", ["comment_id"], unique=False)

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names(schema="public"))

    if {"subreddits", "posts"}.issubset(existing_tables):
        op.execute(
            sa.text(
                """
                INSERT INTO source_targets (
                    source, target_type, target_key, display_name, description,
                    monitor_enabled, fetch_interval, options, last_fetched_at,
                    created_at, updated_at
                )
                SELECT
                    'reddit',
                    'subreddit',
                    s.name,
                    s.name,
                    s.description,
                    COALESCE(s.monitor_enabled, false),
                    COALESCE(s.fetch_interval, 60),
                    '{}'::jsonb,
                    s.last_fetched_at,
                    COALESCE(s.created_at, now()),
                    now()
                FROM subreddits s
                WHERE s.name IS NOT NULL
                ON CONFLICT (source, target_type, target_key) DO UPDATE
                SET
                    display_name = EXCLUDED.display_name,
                    description = EXCLUDED.description,
                    monitor_enabled = EXCLUDED.monitor_enabled,
                    fetch_interval = EXCLUDED.fetch_interval,
                    last_fetched_at = EXCLUDED.last_fetched_at,
                    updated_at = now()
                """
            )
        )

        op.execute(
            sa.text(
                """
                INSERT INTO source_items (
                    target_id, source, external_id, item_type, title, title_zh,
                    content, content_zh, author, url, score, num_comments,
                    created_at, fetched_at
                )
                SELECT
                    st.id,
                    'reddit',
                    p.reddit_id,
                    'post',
                    COALESCE(p.title, '(untitled)'),
                    p.title_zh,
                    p.content,
                    p.content_zh,
                    p.author,
                    p.url,
                    COALESCE(p.score, 0),
                    COALESCE(p.num_comments, 0),
                    COALESCE(p.created_at, p.fetched_at, now()),
                    COALESCE(p.fetched_at, now())
                FROM posts p
                LEFT JOIN subreddits s
                    ON s.id = p.subreddit_id
                LEFT JOIN source_targets st
                    ON st.source = 'reddit'
                   AND st.target_type = 'subreddit'
                   AND st.target_key = s.name
                WHERE p.reddit_id IS NOT NULL
                ON CONFLICT (source, external_id) DO UPDATE
                SET
                    target_id = EXCLUDED.target_id,
                    title = EXCLUDED.title,
                    title_zh = EXCLUDED.title_zh,
                    content = EXCLUDED.content,
                    content_zh = EXCLUDED.content_zh,
                    author = EXCLUDED.author,
                    url = EXCLUDED.url,
                    score = EXCLUDED.score,
                    num_comments = EXCLUDED.num_comments,
                    created_at = EXCLUDED.created_at,
                    fetched_at = EXCLUDED.fetched_at
                """
            )
        )

    if {"post_payloads", "posts"}.issubset(existing_tables):
        op.execute(
            sa.text(
                """
                INSERT INTO source_item_payloads (
                    item_id, source, external_id, payload, fetched_at
                )
                SELECT
                    si.id,
                    'reddit',
                    pp.reddit_id,
                    pp.payload,
                    COALESCE(pp.fetched_at, now())
                FROM post_payloads pp
                JOIN source_items si
                    ON si.source = 'reddit'
                   AND si.external_id = pp.reddit_id
                WHERE pp.reddit_id IS NOT NULL
                ON CONFLICT (item_id) DO UPDATE
                SET
                    source = EXCLUDED.source,
                    external_id = EXCLUDED.external_id,
                    payload = EXCLUDED.payload,
                    fetched_at = EXCLUDED.fetched_at
                """
            )
        )

    if {"comments", "posts"}.issubset(existing_tables):
        op.execute(
            sa.text(
                """
                INSERT INTO source_comments (
                    item_id, source, external_id, content, content_zh, author,
                    score, parent_id, depth, created_at, fetched_at
                )
                SELECT
                    si.id,
                    'reddit',
                    c.reddit_id,
                    COALESCE(c.content, ''),
                    c.content_zh,
                    c.author,
                    COALESCE(c.score, 0),
                    NULL,
                    COALESCE(c.depth, 0),
                    COALESCE(c.created_at, c.fetched_at, now()),
                    COALESCE(c.fetched_at, now())
                FROM comments c
                JOIN posts p
                    ON p.id = c.post_id
                JOIN source_items si
                    ON si.source = 'reddit'
                   AND si.external_id = p.reddit_id
                WHERE c.reddit_id IS NOT NULL
                ON CONFLICT (source, external_id) DO UPDATE
                SET
                    item_id = EXCLUDED.item_id,
                    content = EXCLUDED.content,
                    content_zh = EXCLUDED.content_zh,
                    author = EXCLUDED.author,
                    score = EXCLUDED.score,
                    depth = EXCLUDED.depth,
                    created_at = EXCLUDED.created_at,
                    fetched_at = EXCLUDED.fetched_at
                """
            )
        )

        op.execute(
            sa.text(
                """
                UPDATE source_comments sc
                SET parent_id = sc_parent.id
                FROM comments c
                JOIN comments c_parent
                  ON c.parent_id = c_parent.id
                JOIN source_comments sc_parent
                  ON sc_parent.source = 'reddit'
                 AND sc_parent.external_id = c_parent.reddit_id
                WHERE sc.source = 'reddit'
                  AND sc.external_id = c.reddit_id
                  AND c.parent_id IS NOT NULL
                """
            )
        )

    if {"comment_payloads", "comments"}.issubset(existing_tables):
        op.execute(
            sa.text(
                """
                INSERT INTO source_comment_payloads (
                    comment_id, source, external_id, payload, fetched_at
                )
                SELECT
                    sc.id,
                    'reddit',
                    cp.reddit_id,
                    cp.payload,
                    COALESCE(cp.fetched_at, now())
                FROM comment_payloads cp
                JOIN source_comments sc
                    ON sc.source = 'reddit'
                   AND sc.external_id = cp.reddit_id
                WHERE cp.reddit_id IS NOT NULL
                ON CONFLICT (comment_id) DO UPDATE
                SET
                    source = EXCLUDED.source,
                    external_id = EXCLUDED.external_id,
                    payload = EXCLUDED.payload,
                    fetched_at = EXCLUDED.fetched_at
                """
            )
        )

    if {"post_tags", "posts"}.issubset(existing_tables):
        op.execute(
            sa.text(
                """
                INSERT INTO source_item_tags (source_item_id, tag_id)
                SELECT DISTINCT
                    si.id,
                    pt.tag_id
                FROM post_tags pt
                JOIN posts p
                  ON p.id = pt.post_id
                JOIN source_items si
                  ON si.source = 'reddit'
                 AND si.external_id = p.reddit_id
                ON CONFLICT (source_item_id, tag_id) DO NOTHING
                """
            )
        )

    if {"analyses", "comments"}.issubset(existing_tables):
        op.execute(
            sa.text(
                """
                INSERT INTO source_analyses (
                    comment_id, pain_points, user_needs, opportunities,
                    model_used, is_valuable, created_at
                )
                SELECT
                    sc.id,
                    a.pain_points::text,
                    a.user_needs::text,
                    a.opportunities::text,
                    a.model_used,
                    COALESCE(a.is_valuable, 0),
                    COALESCE(a.created_at, now())
                FROM analyses a
                JOIN comments c
                  ON c.id = a.comment_id
                JOIN source_comments sc
                  ON sc.source = 'reddit'
                 AND sc.external_id = c.reddit_id
                """
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("source_analyses")
    op.drop_table("source_item_tags")
    op.drop_table("source_comment_payloads")
    op.drop_table("source_item_payloads")
    op.drop_table("source_comments")
    op.drop_table("source_items")
    op.drop_table("source_targets")
