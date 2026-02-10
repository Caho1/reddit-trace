# Trace Hub

多平台社区热点与用户需求挖掘系统（当前支持 `Reddit` + `Hacker News`）。

通过统一抓取、统一入库、统一查询和 AI 分析，持续沉淀可检索的用户痛点、需求与机会信号。

## 当前能力

- 多源抓取：`Reddit`、`Hacker News`
- 统一目标模型：`source + target_type + target_key`
- 统一内容模型：`source_items / source_comments`
- 标签体系：支持筛选与人工归类
- 定时调度：基于目标的自动抓取
- AI 分析：价值筛选 + 深度分析（可扩展 provider）

## 架构说明（多源可扩展）

### 核心表（推荐使用）

- `source_targets`：监控目标
- `source_items`：统一内容实体（帖子/故事）
- `source_comments`：统一评论实体
- `source_item_payloads` / `source_comment_payloads`：原始 payload
- `source_item_tags`：统一内容与标签关联

### 兼容表（逐步迁移）

- `subreddits / posts / comments` 及其关联表仍保留，用于兼容旧接口。

### 适配器模式

- 每个平台实现 `SourceAdapter`
- 注册中心统一管理平台能力
- 新增平台时，优先复用统一抓取/入库/调度链路

## 环境要求

- Python `3.12+`
- Node.js `18+`
- PostgreSQL `14+`
- `uv`（推荐用于 Python 依赖管理与运行）

## 快速开始

### 1) 克隆仓库

```bash
git clone https://github.com/Caho1/reddit-trace.git
cd reddit-trace
```

### 2) 后端初始化

```bash
cd backend
uv sync
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac
```

编辑 `backend/.env`，至少配置：

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
AUTO_CREATE_TABLES=false

# 如果访问 Reddit 需要代理
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

执行迁移：

```bash
uv run alembic upgrade head
```

启动后端：

```bash
uv run uvicorn app.main:app --reload
```

后端文档：`http://localhost:8000/docs`

### 3) 前端初始化

```bash
cd ../frontend
npm install
npm run dev
```

前端地址：`http://localhost:5173`

## 关键 API（推荐走统一接口）

### 查看平台能力

```bash
curl http://localhost:8000/api/sources/capabilities
```

### 创建监控目标

```bash
curl -X POST http://localhost:8000/api/sources/targets \
  -H "Content-Type: application/json" \
  -d '{
    "source": "hackernews",
    "target_type": "feed",
    "target_key": "topstories",
    "display_name": "HN Top Stories",
    "monitor_enabled": true,
    "fetch_interval": 60
  }'
```

### 触发抓取

```bash
curl -X POST http://localhost:8000/api/sources/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "source": "hackernews",
    "target_type": "feed",
    "target_key": "topstories",
    "limit": 30,
    "include_comments": false
  }'
```

### 查询内容（兼容返回结构）

```bash
curl "http://localhost:8000/api/posts?source=hackernews&limit=20"
```

> `POSTS` 接口已支持 `"/api/posts"` 与 `"/api/posts/"`，推荐使用无尾斜杠路径。

## 兼容接口（保留）

- `POST /api/crawler/fetch-post`
- `POST /api/crawler/fetch-subreddit`
- `GET/PUT /api/posts/*`
- `GET/POST/PATCH/DELETE /api/subreddits/*`

这些接口仍可用，但新功能建议优先接入 `sources/*`。

## 新平台接入指南

1. 在 `backend/app/services/sources/` 新增适配器文件（实现 `SourceAdapter`）。
2. 在 `source_registry_service` 注册该适配器。
3. 前端补充目标类型与抓取表单（`CrawlerPage` / `SubredditsPage`）。
4. 复用统一抓取、统一入库、统一查询链路，无需再建一套独立表结构。

## 常用开发命令

### 后端

```bash
cd backend
uv run alembic current
uv run alembic revision -m "your_migration"
uv run alembic upgrade head
uv run python -m compileall app
```

### 前端

```bash
cd frontend
npm run typecheck
npm run build
```

## 项目结构

```text
reddit-trace/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   └── sources/      # 平台适配器
│   │   ├── llm/
│   │   └── main.py
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
└── README.md
```

## License

Apache-2.0
