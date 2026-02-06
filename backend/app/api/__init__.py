from fastapi import APIRouter
from app.api import subreddits, posts, analysis, tags, crawler, dashboard

router = APIRouter()

router.include_router(subreddits.router, prefix="/subreddits", tags=["subreddits"])
router.include_router(posts.router, prefix="/posts", tags=["posts"])
router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
router.include_router(tags.router, prefix="/tags", tags=["tags"])
router.include_router(crawler.router, prefix="/crawler", tags=["crawler"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
