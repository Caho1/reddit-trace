# Reddit Trace

基于 **Reddit JSON Hack** 方法论的用户需求挖掘系统。

通过自动抓取 Reddit 用户真实对话，利用 AI 智能分析提取用户痛点、需求和创业机会。

## 核心价值

- **真实性**: 获取用户在社区的真实讨论，而非调研问卷
- **深度**: 完整的对话线程和嵌套评论分析
- **规模化**: 定时自动监控，建立需求数据库
- **智能化**: AI 两阶段分析，精准提取有价值信息

## 功能特性

### 数据采集
- 单个帖子 URL 抓取
- 整个版块热门/最新帖子抓取
- 定时自动监控指定版块
- 支持代理配置

### AI 分析
- 多模型支持（OpenAI / Claude / Ollama）
- 两阶段分析：批量筛选 + 深度分析
- 提取维度：用户痛点、用户需求、创业机会
- 双语存储：英文原文 + 中文翻译

### 数据管理
- 标签/分类系统
- 数据导出（Excel/CSV/JSON）
- Markdown 报告生成

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 | PostgreSQL |
| ORM | SQLAlchemy 2.0 (async) |
| 定时任务 | APScheduler |
| AI 集成 | OpenAI / Anthropic SDK |
| HTTP 客户端 | httpx (async) |

## 快速开始

### 环境要求

- Python 3.10+
- PostgreSQL 14+

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/Caho1/reddit-trace.git
cd reddit-trace
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
cd backend
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/reddit_trace

# 代理（访问 Reddit 需要）
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890

# AI 模型 API Key（至少配置一个）
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
```

5. **创建数据库**
```bash
createdb reddit_trace
```

6. **启动服务**
```bash
uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

## API 示例

### 抓取单个帖子
```bash
curl -X POST http://localhost:8000/api/crawler/fetch-post \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.reddit.com/r/SaaS/comments/xxx/title"}'
```

### 抓取版块帖子
```bash
curl -X POST http://localhost:8000/api/crawler/fetch-subreddit \
  -H "Content-Type: application/json" \
  -d '{"name": "SaaS", "sort": "hot", "limit": 25}'
```

### 添加监控版块
```bash
curl -X POST http://localhost:8000/api/subreddits \
  -H "Content-Type: application/json" \
  -d '{"name": "SaaS", "monitor_enabled": true, "fetch_interval": 60}'
```

## 项目结构

```
reddit-trace/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # 业务逻辑
│   │   ├── llm/          # LLM 集成
│   │   ├── main.py       # 入口文件
│   │   ├── config.py     # 配置管理
│   │   └── database.py   # 数据库连接
│   ├── requirements.txt
│   └── .env.example
├── PLAN.md               # 详细设计文档
└── README.md
```

## Reddit JSON Hack 方法论

**核心逻辑**: 在任意 Reddit 帖子 URL 后加 `/.json`，即可获取完整的 JSON 数据。

```
原始 URL: https://www.reddit.com/r/SaaS/comments/abc123/title
JSON URL: https://www.reddit.com/r/SaaS/comments/abc123/title/.json
```

**分析重点**:
- 用户抱怨什么 → 痛点
- 用户希望什么 → 需求
- 用户的变通方案 → 市场机会

> $10k MRR 的种子可能就藏在这些"抱怨"里。

## License

Apache-2.0
