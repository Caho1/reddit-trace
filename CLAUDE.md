# Reddit Trace 项目指南

## 项目概述

Reddit 用户需求挖掘系统，基于 Reddit JSON Hack 方法论。

**核心功能**：
- 自动抓取 Reddit 帖子和评论
- AI 两阶段分析（筛选 + 深度分析）
- 提取用户痛点、需求、创业机会
- 定时监控指定版块

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy 2.0 (async) |
| 数据库 | PostgreSQL |
| 定时任务 | APScheduler |
| AI | OpenAI 兼容 API (apimart.ai) |
| 包管理 | uv |

## 项目结构

```
backend/
├── app/
│   ├── main.py          # FastAPI 入口，启动定时任务
│   ├── config.py        # 配置管理，读取 .env
│   ├── database.py      # 异步数据库连接
│   ├── models/          # SQLAlchemy 模型
│   ├── schemas/         # Pydantic 请求/响应模型
│   ├── api/             # API 路由
│   ├── services/        # 业务逻辑
│   │   ├── crawler.py   # Reddit 数据抓取
│   │   ├── analyzer.py  # AI 分析服务
│   │   └── scheduler.py # 定时任务调度
│   └── llm/             # LLM 集成
│       ├── base.py      # 抽象基类
│       ├── openai.py    # OpenAI 兼容实现
│       └── claude.py    # Claude 实现
├── pyproject.toml       # 依赖管理
└── .env                 # 环境变量（不提交）
```

## 常用命令

```bash
# 进入后端目录
cd backend

# 安装依赖
uv sync

# 启动开发服务器
uv run uvicorn app.main:app --reload

# 查看 API 文档
# http://localhost:8000/docs
```

## 开发指南

### 添加新 API

1. 在 `app/api/` 创建路由文件
2. 在 `app/api/__init__.py` 注册路由
3. 如需新模型，在 `app/models/` 和 `app/schemas/` 添加

### AI 分析流程

```
评论 → 阶段1筛选(gemini-2.0-flash) → 有价值?
                                      ↓ 是
                              阶段2深度分析(gemini-2.5-pro-preview)
                                      ↓
                              提取: 痛点/需求/机会
```

### Reddit 抓取

- JSON API: 在 URL 后加 `/.json`
- 需要代理访问
- Rate limit: 每分钟 60 次请求

## 代码规范

- 使用 async/await 异步编程
- 数据库操作使用 SQLAlchemy 2.0 async 语法
- API 响应使用 Pydantic schema
- 配置通过 .env 环境变量管理

## 待完成功能

- [ ] 完善数据保存逻辑（抓取后存入数据库）
- [ ] 翻译功能（英文→中文双语存储）
- [ ] 报告生成（Markdown 格式）
- [ ] 数据导出（Excel/CSV）
- [ ] 前端界面（React）
