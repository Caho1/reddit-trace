# Reddit Trace – Data Flow

## Data Flow Diagram

```mermaid
flowchart TD
  %% Frontend
  subgraph FE[Frontend (React)]
    FE_Crawler[抓取页 CrawlerPage]
    FE_Posts[帖子页 PostsPage]
    FE_Tags[标签页 TagsPage]
    FE_Dashboard[仪表盘 DashboardPage]
    FE_SubMon[板块监控 SubredditsPage]
  end

  %% Backend
  subgraph BE[Backend (FastAPI)]
    API_Crawler[API /api/crawler/*]
    API_Posts[API /api/posts/*]
    API_Tags[API /api/tags/*]
    API_Sub[API /api/subreddits/*]
    API_Dash[API /api/dashboard/stats]

    SVC_Crawler[services.crawler\nRedditCrawler]
    SVC_Ingest[services.ingest\nsave_subreddit_posts / save_post_comments]
    SVC_Scheduler[services.scheduler\nAPScheduler job]
  end

  %% External
  subgraph EX[External Services]
    EX_Reddit[(Reddit API)]
    EX_LLM[(LLM Providers)]
  end

  %% Database
  subgraph DB[PostgreSQL]
    T_subreddits[(subreddits)]
    T_posts[(posts)]
    T_comments[(comments)]
    T_tags[(tags)]
    T_post_tags[(post_tags)]
    T_post_payloads[(post_payloads)]
    T_comment_payloads[(comment_payloads)]
    T_analyses[(analyses)]
    T_analysis_tags[(analysis_tags)]
  end

  %% Crawler page: fetch -> reddit -> ingest -> db
  FE_Crawler -->|POST fetch-subreddit / fetch-post| API_Crawler
  API_Crawler --> SVC_Crawler -->|HTTP| EX_Reddit
  API_Crawler -->|落库| SVC_Ingest --> DB

  %% Posts page: read from db + tag filter
  FE_Posts -->|GET /api/posts?subreddit_id&tag_id| API_Posts --> DB
  FE_Posts -->|PUT /api/posts/{id}/tags| API_Posts --> DB

  %% Tag management
  FE_Tags --> API_Tags --> DB

  %% Subreddit monitor management
  FE_SubMon --> API_Sub --> DB

  %% Dashboard: stats + recent lists
  FE_Dashboard --> API_Dash --> DB
  FE_Dashboard -->|GET /api/posts /api/analysis| BE --> DB

  %% Scheduler: periodically fetch monitored subreddits, then ingest into db
  SVC_Scheduler -->|SELECT monitor_enabled| T_subreddits
  SVC_Scheduler --> SVC_Crawler -->|HTTP| EX_Reddit
  SVC_Scheduler -->|落库| SVC_Ingest --> DB

  %% Analysis (future/optional): comments -> LLM -> analyses/tags
  T_comments --> EX_LLM --> T_analyses --> T_analysis_tags
```

## Key Guarantees (Why this avoids wasting Reddit API)

- 抓取接口在返回数据给前端的同时，会把帖子/评论落库（并做去重更新），因此抓取结果不会“只展示一次就丢失”。  
- “帖子”页与“仪表盘”只读数据库，不会再重复请求 Reddit。
- 标签既可用于筛选，也可用于手动给帖子分类；抓取时会把 Reddit 的 `link_flair_text` 自动转成标签并绑定到帖子（不额外消耗 Reddit API）。

