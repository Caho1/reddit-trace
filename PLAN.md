# Reddit Trace - 用户需求挖掘系统

## 项目概述

基于 Reddit JSON Hack 方法论，构建一个全自动化的用户需求挖掘系统。

## 需求确认

| 需求项 | 选择 |
|--------|------|
| 核心功能 | 全自动化系统 |
| 数据采集 | 定时自动监控指定版块 |
| AI模型 | 多模型支持（OpenAI/Claude/Ollama） |
| 分析维度 | 用户痛点、用户需求、创业机会识别 |
| 分析粒度 | 两阶段分析（先筛选后深度分析） |
| 数据存储 | PostgreSQL |
| Web界面 | FastAPI + React |
| 网络访问 | 需要代理支持 |
| 内容翻译 | 双语存储（英文原文+中文翻译） |
| 用户系统 | 无（单用户使用） |
| 报告格式 | Markdown |
| 数据可视化 | 分类统计图表、时间趋势图、词云图 |

## 技术栈

- **后端**: Python + FastAPI
- **前端**: React + TypeScript + Ant Design
- **数据库**: PostgreSQL
- **定时任务**: APScheduler
- **AI分析**: 多模型支持（OpenAI、Claude、本地模型）

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Frontend (React)                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ 监控管理 │ │ 数据浏览 │ │ 分析报告 │ │ 系统设置 │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 数据采集模块 │ │ AI分析模块  │ │ 报告生成模块 │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ 版块配置 │ │ 帖子数据 │ │ 分析结果 │ │ 标签分类 │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
reddit-trace/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   ├── models/              # 数据模型
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/                 # API 路由
│   │   ├── services/            # 业务逻辑
│   │   └── llm/                 # LLM 集成
│   ├── alembic/                 # 数据库迁移
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # React 组件
│   │   ├── pages/               # 页面
│   │   ├── services/            # API 调用
│   │   └── stores/              # 状态管理
│   ├── package.json
│   └── vite.config.ts
├── PLAN.md
└── README.md
```

## 核心功能模块

### 模块1: 数据采集 (Crawler)

**功能**:
- 支持单个帖子URL抓取
- 支持整个subreddit热门/最新帖子抓取
- 定时自动监控指定版块
- 增量抓取（避免重复）

**实现要点**:
- 使用 httpx 异步请求
- Reddit JSON API: `{url}/.json`
- 遵守 rate limit（每分钟60次请求）
- 解析嵌套评论结构
- **代理支持**: 配置 HTTP/SOCKS5 代理访问 Reddit

### 模块2: AI分析 (Analyzer)

**功能**:
- 多模型支持（OpenAI/Claude/Ollama）
- 提取用户痛点
- 提取用户需求
- 识别创业机会
- **双语存储**: 保存英文原文和中文翻译

**两阶段分析流程**:
```
阶段1: 批量筛选
├── 输入: 多条评论（批量）
├── 目的: 快速识别有价值的评论
├── 输出: 标记为"有价值"或"无价值"
└── 模型: 使用较便宜的模型（如 GPT-3.5）

阶段2: 深度分析
├── 输入: 阶段1筛选出的有价值评论
├── 目的: 详细提取痛点、需求、机会
├── 输出: 结构化分析结果
└── 模型: 使用更强的模型（如 GPT-4/Claude）
```

**分析Prompt模板**:
```
分析以下Reddit评论，提取：
1. 用户痛点：用户抱怨什么、什么让他们不满
2. 用户需求：用户希望有什么、愿意付费买什么
3. 创业机会：基于痛点和需求，可能的产品/服务机会

评论内容：
{comment_text}

请以JSON格式返回分析结果。
```

### 模块3: 定时调度 (Scheduler)

**功能**:
- 配置监控的subreddit列表
- 设置抓取频率（每小时/每天等）
- 自动触发抓取和分析
- 任务状态监控

### 模块4: 数据管理

**功能**:
- 标签/分类系统
- 高级搜索和筛选
- 数据导出（Excel/CSV/JSON）
- 报告生成（Markdown）

### 模块5: 前端可视化

**图表功能**:
- **分类统计图表**: 痛点/需求/机会的分布饼图、柱状图
- **时间趋势图**: 数据量随时间的变化折线图
- **词云图**: 高频关键词可视化

**技术选型**:
- 图表库: ECharts 或 Recharts
- 词云: wordcloud2.js

## 数据库设计

### 表结构

**subreddits** - 监控的版块
| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| name | VARCHAR(100) | 版块名称，如 "SaaS" |
| description | TEXT | 版块描述 |
| monitor_enabled | BOOLEAN | 是否启用监控 |
| fetch_interval | INTEGER | 抓取间隔（分钟） |
| last_fetched_at | TIMESTAMP | 最后抓取时间 |

**posts** - 帖子
| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| subreddit_id | INTEGER | 关联版块 |
| reddit_id | VARCHAR(20) | Reddit帖子ID |
| title | VARCHAR(500) | 标题 |
| content | TEXT | 内容 |
| author | VARCHAR(100) | 作者 |
| url | VARCHAR(500) | 原始链接 |
| score | INTEGER | 点赞数 |
| num_comments | INTEGER | 评论数 |
| created_at | TIMESTAMP | 创建时间 |

**comments** - 评论
| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| post_id | INTEGER | 关联帖子 |
| reddit_id | VARCHAR(20) | Reddit评论ID |
| content | TEXT | 评论内容（英文原文） |
| content_zh | TEXT | 评论内容（中文翻译） |
| author | VARCHAR(100) | 作者 |
| score | INTEGER | 点赞数 |
| parent_id | INTEGER | 父评论ID（嵌套） |
| depth | INTEGER | 嵌套深度 |
| created_at | TIMESTAMP | 创建时间 |

**analyses** - 分析结果
| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| comment_id | INTEGER | 关联评论 |
| pain_points | JSONB | 用户痛点列表 |
| user_needs | JSONB | 用户需求列表 |
| opportunities | JSONB | 创业机会列表 |
| model_used | VARCHAR(50) | 使用的AI模型 |
| created_at | TIMESTAMP | 分析时间 |

**tags** - 标签
| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| name | VARCHAR(50) | 标签名称 |
| color | VARCHAR(20) | 标签颜色 |
| description | TEXT | 标签描述 |

## 实现步骤

### 阶段1: 后端基础架构
1. 初始化 FastAPI 项目结构
2. 配置 PostgreSQL 数据库连接
3. 创建数据模型和迁移脚本
4. 实现基础 CRUD API

### 阶段2: 数据采集模块
1. 实现 Reddit JSON API 抓取
2. 解析帖子和评论数据
3. 实现增量抓取逻辑
4. 添加 rate limit 控制

### 阶段3: AI分析模块
1. 设计 LLM 抽象接口
2. 实现 OpenAI 适配器
3. 实现 Claude 适配器
4. 实现分析 Prompt 和结果解析

### 阶段4: 定时任务
1. 集成 APScheduler
2. 实现监控任务配置
3. 实现自动抓取和分析流程

### 阶段5: 前端界面
1. 初始化 React + Vite 项目
2. 实现监控管理页面
3. 实现数据浏览页面
4. 实现分析报告页面
5. 实现系统设置页面

### 阶段6: 高级功能
1. 标签/分类系统
2. 数据导出功能
3. 报告生成功能

## 依赖清单

### 后端 (requirements.txt)
```
fastapi>=0.109.0
uvicorn>=0.27.0
sqlalchemy>=2.0.0
alembic>=1.13.0
asyncpg>=0.29.0
httpx>=0.26.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
apscheduler>=3.10.0
openai>=1.10.0
anthropic>=0.18.0
python-dotenv>=1.0.0
```

### 前端 (package.json 主要依赖)
```
react, react-dom, typescript
@ant-design/pro-components
axios, @tanstack/react-query
react-router-dom
zustand (状态管理)
```

## 配置文件示例

### .env 配置
```env
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/reddit_trace

# 代理配置
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1

# Claude
ANTHROPIC_API_KEY=sk-ant-xxx

# Ollama (本地模型)
OLLAMA_BASE_URL=http://localhost:11434

# 默认使用的模型
DEFAULT_LLM_PROVIDER=openai
DEFAULT_SCREENING_MODEL=gpt-3.5-turbo
DEFAULT_ANALYSIS_MODEL=gpt-4
```

## 验证方式

1. **数据采集验证**: 配置代理后，输入Reddit URL，验证能正确抓取帖子和评论
2. **翻译验证**: 验证英文内容能正确翻译并双语存储
3. **AI分析验证**: 对抓取的评论运行两阶段分析，验证能正确提取痛点/需求
4. **定时任务验证**: 配置监控任务，验证能按时自动执行
5. **前端验证**: 通过Web界面完成完整的操作流程，验证图表正常显示
