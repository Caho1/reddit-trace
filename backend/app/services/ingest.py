from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.comment import Comment
from app.models.payload import CommentPayload, PostPayload
from app.models.post import Post
from app.models.subreddit import Subreddit
from app.models.tag import Tag

logger = get_logger("reddit_trace.ingest")

REDDIT_WEB_BASE_URL = "https://www.reddit.com"


def normalize_subreddit_name(name: str) -> str:
    n = (name or "").strip()
    if n.lower().startswith("r/"):
        n = n[2:]
    return n.strip()


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def build_reddit_permalink(permalink: Optional[str]) -> Optional[str]:
    if not permalink:
        return None
    if permalink.startswith("http://") or permalink.startswith("https://"):
        return permalink
    if not permalink.startswith("/"):
        permalink = "/" + permalink
    return f"{REDDIT_WEB_BASE_URL}{permalink}"


async def upsert_subreddit(db: AsyncSession, *, name: str, fetched_at: datetime) -> Subreddit:
    normalized = normalize_subreddit_name(name)
    if not normalized:
        raise ValueError("subreddit_name is required")
    result = await db.execute(select(Subreddit).where(Subreddit.name == normalized))
    subreddit = result.scalar_one_or_none()
    if not subreddit:
        subreddit = Subreddit(name=normalized, monitor_enabled=False, fetch_interval=60)
        db.add(subreddit)
        await db.flush()

    subreddit.last_fetched_at = fetched_at
    return subreddit


async def _get_or_create_tags(db: AsyncSession, names: Iterable[str]) -> Dict[str, Tag]:
    normalized = {str(n).strip() for n in names if str(n).strip()}
    if not normalized:
        return {}

    result = await db.execute(select(Tag).where(Tag.name.in_(normalized)))
    existing = {t.name: t for t in result.scalars().all()}

    for name in sorted(normalized):
        if name in existing:
            continue
        tag = Tag(name=name)
        db.add(tag)
        existing[name] = tag

    await db.flush()
    return existing


async def save_subreddit_posts(
    db: AsyncSession,
    *,
    subreddit_name: str,
    posts: List[Dict[str, Any]],
    fetched_at: Optional[datetime] = None,
) -> Tuple[Subreddit, int, int]:
    fetched_at = fetched_at or datetime.now(timezone.utc)
    subreddit = await upsert_subreddit(db, name=subreddit_name, fetched_at=fetched_at)

    reddit_ids = [p.get("id") for p in posts if p.get("id")]
    existing_posts: Dict[str, Post] = {}
    if reddit_ids:
        result = await db.execute(select(Post).where(Post.reddit_id.in_(reddit_ids)))
        existing_posts = {p.reddit_id: p for p in result.scalars().all()}

    tag_map = await _get_or_create_tags(
        db,
        names=[p.get("link_flair_text") for p in posts if p.get("link_flair_text")],
    )

    created = 0
    updated = 0
    for post_data in posts:
        reddit_id = post_data.get("id")
        if not reddit_id:
            continue

        created_at = ensure_utc(post_data.get("created_utc")) or fetched_at
        url = build_reddit_permalink(post_data.get("permalink")) or post_data.get("url") or ""

        title = post_data.get("title") or ""
        author = post_data.get("author") or "[deleted]"
        content = post_data.get("selftext") or None

        score = int(post_data.get("score") or 0)
        num_comments = int(post_data.get("num_comments") or 0)

        post = existing_posts.get(reddit_id)
        if post:
            updated += 1
            post.subreddit_id = subreddit.id
            post.title = title
            post.content = content
            post.author = author
            post.url = url
            post.score = score
            post.num_comments = num_comments
            post.created_at = created_at
            post.fetched_at = fetched_at
        else:
            created += 1
            post = Post(
                subreddit_id=subreddit.id,
                reddit_id=reddit_id,
                title=title,
                content=content,
                author=author,
                url=url,
                score=score,
                num_comments=num_comments,
                created_at=created_at,
                fetched_at=fetched_at,
            )
            db.add(post)
            existing_posts[reddit_id] = post

    await db.flush()

    # Upsert payload + flair tags
    payload_map: Dict[str, PostPayload] = {}
    if reddit_ids:
        result = await db.execute(select(PostPayload).where(PostPayload.reddit_id.in_(reddit_ids)))
        payload_map = {p.reddit_id: p for p in result.scalars().all()}

    for post_data in posts:
        reddit_id = post_data.get("id")
        if not reddit_id:
            continue
        post = existing_posts.get(reddit_id)
        if not post:
            continue

        payload = payload_map.get(reddit_id)
        if payload:
            payload.post_id = post.id
            payload.payload = jsonable_encoder(post_data)
            payload.fetched_at = fetched_at
        else:
            db.add(
                PostPayload(
                    post_id=post.id,
                    reddit_id=reddit_id,
                    payload=jsonable_encoder(post_data),
                    fetched_at=fetched_at,
                )
            )

        flair = post_data.get("link_flair_text")
        if flair:
            tag = tag_map.get(str(flair).strip())
            if tag:
                post.tags.add(tag)

    await db.flush()
    return subreddit, created, updated


async def save_post_comments(
    db: AsyncSession,
    *,
    post: Post,
    comments: List[Dict[str, Any]],
    fetched_at: Optional[datetime] = None,
) -> Tuple[int, int]:
    fetched_at = fetched_at or datetime.now(timezone.utc)

    reddit_ids = [c.get("id") for c in comments if c.get("id")]
    existing_comments: Dict[str, Comment] = {}
    if reddit_ids:
        result = await db.execute(select(Comment).where(Comment.reddit_id.in_(reddit_ids)))
        existing_comments = {c.reddit_id: c for c in result.scalars().all()}

    created = 0
    updated = 0
    for comment_data in comments:
        reddit_id = comment_data.get("id")
        if not reddit_id:
            continue

        created_at = ensure_utc(comment_data.get("created_utc")) or fetched_at
        author = comment_data.get("author") or "[deleted]"
        content = comment_data.get("body") or ""
        score = int(comment_data.get("score") or 0)
        depth = int(comment_data.get("depth") or 0)

        comment = existing_comments.get(reddit_id)
        if comment:
            updated += 1
            comment.post_id = post.id
            comment.content = content
            comment.author = author
            comment.score = score
            comment.depth = depth
            comment.created_at = created_at
            comment.fetched_at = fetched_at
        else:
            created += 1
            comment = Comment(
                post_id=post.id,
                reddit_id=reddit_id,
                content=content,
                author=author,
                score=score,
                depth=depth,
                created_at=created_at,
                fetched_at=fetched_at,
            )
            db.add(comment)
            existing_comments[reddit_id] = comment

    await db.flush()

    # Fix parent_id mapping (Reddit uses "t1_xxx" / "t3_xxx")
    for comment_data in comments:
        reddit_id = comment_data.get("id")
        if not reddit_id:
            continue
        comment = existing_comments.get(reddit_id)
        if not comment:
            continue

        parent_id = comment_data.get("parent_id")
        parent_db_id = None
        if isinstance(parent_id, str) and parent_id.startswith("t1_"):
            parent_reddit_id = parent_id[3:]
            parent = existing_comments.get(parent_reddit_id)
            if parent:
                parent_db_id = parent.id
        comment.parent_id = parent_db_id

    await db.flush()

    # Upsert payload
    payload_map: Dict[str, CommentPayload] = {}
    if reddit_ids:
        result = await db.execute(
            select(CommentPayload).where(CommentPayload.reddit_id.in_(reddit_ids))
        )
        payload_map = {p.reddit_id: p for p in result.scalars().all()}

    for comment_data in comments:
        reddit_id = comment_data.get("id")
        if not reddit_id:
            continue
        comment = existing_comments.get(reddit_id)
        if not comment:
            continue

        payload = payload_map.get(reddit_id)
        if payload:
            payload.comment_id = comment.id
            payload.payload = jsonable_encoder(comment_data)
            payload.fetched_at = fetched_at
        else:
            db.add(
                CommentPayload(
                    comment_id=comment.id,
                    reddit_id=reddit_id,
                    payload=jsonable_encoder(comment_data),
                    fetched_at=fetched_at,
                )
            )

    await db.flush()
    return created, updated
