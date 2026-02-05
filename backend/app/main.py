from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import router
from app.database import engine, Base
from app.services import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表（开发环境用，生产环境用 alembic）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 启动定时任务调度器
    scheduler_service.start()
    yield
    # 关闭定时任务调度器
    scheduler_service.stop()


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


@app.get("/")
async def root():
    return {"message": "Reddit Trace API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
