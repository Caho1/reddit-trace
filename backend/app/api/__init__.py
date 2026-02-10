from fastapi import APIRouter
from app.api import (
    analyses_api,
    crawler_api,
    dashboard_api,
    posts_api,
    sources_api,
    subreddits_api,
    tags_api,
)

router = APIRouter()

router.include_router(subreddits_api.router, prefix="/subreddits", tags=["subreddits"])
router.include_router(posts_api.router, prefix="/posts", tags=["posts"])
router.include_router(analyses_api.router, prefix="/analysis", tags=["analysis"])
router.include_router(tags_api.router, prefix="/tags", tags=["tags"])
router.include_router(crawler_api.router, prefix="/crawler", tags=["crawler"])
router.include_router(dashboard_api.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(sources_api.router, prefix="/sources", tags=["sources"])
