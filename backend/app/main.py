from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from sqlalchemy.exc import DBAPIError

from app.api import router
from app.database import engine, Base
import app.models  # noqa: F401
from app.services import scheduler_service
from app.services.crawler import crawler as reddit_crawler
from app.logging_config import setup_logging, get_logger

# 初始化日志系统
setup_logging(level="INFO")
logger = get_logger("reddit_trace.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("Reddit Trace 服务启动中...")

    # 启动时创建表（开发环境用，生产环境用 alembic）
    logger.info("[1/2] 初始化数据库...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("[1/2] 数据库初始化完成")

    # 启动定时任务调度器
    logger.info("[2/2] 启动定时任务调度器...")
    scheduler_service.start()
    logger.info("[2/2] 定时任务调度器已启动")

    logger.info("Reddit Trace 服务启动完成!")
    logger.info("=" * 50)
    yield

    # 关闭定时任务调度器
    logger.info("Reddit Trace 服务关闭中...")
    scheduler_service.stop()
    try:
        await reddit_crawler.close()
    except Exception as e:
        logger.warning(f"关闭 HTTP 客户端失败: {type(e).__name__}: {e}", exc_info=True)
    logger.info("服务已关闭")


app = FastAPI(
    title="Reddit Trace",
    description="Reddit 用户需求挖掘系统",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix="/api")


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    request_id = f"{int(start_time * 1000) % 100000:05d}"

    # 记录请求开始
    logger.info(f"[{request_id}] --> {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        logger.info(f"[{request_id}] <-- {response.status_code} ({duration:.0f}ms)")
        return response
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"[{request_id}] <-- ERROR ({duration:.0f}ms): {type(e).__name__}: {e}")
        raise


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(DBAPIError)
async def db_exception_handler(request: Request, exc: DBAPIError):
    logger.error(f"数据库异常: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=503,
        content={
            "error": "DatabaseError",
            "message": "数据库连接异常或暂时不可用，请稍后重试",
            "path": str(request.url.path),
        },
    )


@app.get("/")
async def root():
    return {"message": "Reddit Trace API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
