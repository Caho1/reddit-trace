# Multi-Source Extensible Architecture Plan (Implemented)

## Goal

将原有 Reddit-only 系统升级为可持续扩展的多源监控框架，当前落地 Reddit + Hacker News，两者共享统一抓取/入库/查询/调度接口，后续可低成本扩展第 3 个平台。

## Core Principles

- 统一核心模型：用 `source_targets/source_items/source_comments` 承载平台数据。
- 适配器模式：每个平台实现 `SourceAdapter`，避免业务代码复制。
- 旧接口兼容：保留 `subreddits/posts/crawler`，逐步迁移到 `sources/*`。
- 调度统一：调度器优先消费 `source_targets`，不再绑定 `subreddits`。

## Implemented Data Model

### New Core Tables

- `source_targets`: 监控目标（source + target_type + target_key）
- `source_items`: 统一内容实体（帖子/故事）
- `source_comments`: 统一评论实体
- `source_item_payloads`, `source_comment_payloads`: 原始 payload
- `source_item_tags`: 内容-标签关联

### Legacy Tables Kept (Compatibility)

- `subreddits/posts/comments/post_tags/post_payloads/comment_payloads`
- 仍可读写；新功能默认走统一模型。

## Implemented Backend Modules

### Adapters

- `backend/app/services/sources/base.py`: `SourceAdapter` 抽象
- `backend/app/services/sources/reddit.py`: Reddit 适配器
- `backend/app/services/sources/hackernews.py`: HN 适配器
- `backend/app/services/source_registry.py`: 注册中心

### Ingest + Fetch

- `backend/app/services/source_ingest.py`: 统一 upsert/save
- `backend/app/services/source_fetch.py`: 统一抓取+入库工作流

### API

- 新增 `backend/app/api/sources.py`
  - `GET /api/sources/capabilities`
  - `GET/POST/PATCH/DELETE /api/sources/targets`
  - `POST /api/sources/fetch`
  - `GET /api/sources/items`
  - `GET /api/sources/items/{id}`
  - `GET/PUT /api/sources/items/{id}/tags`
  - `GET /api/sources/items/{id}/comments`

- 兼容层增强：
  - `POST /api/crawler/fetch-item` 新增统一 URL 抓取入口
  - `GET /api/posts` 支持 `source/target_id` 过滤（读取统一模型）

### Scheduler

- `backend/app/services/scheduler.py` 已支持 `source_targets` 统一调度。
- 若发现 legacy `subreddits` 已映射到统一目标，自动跳过重复抓取。

## Implemented Frontend Changes

- `PostsPage`：支持来源筛选 + 统一内容查询 + 统一标签操作。
- `CrawlerPage`：支持 Reddit/HN 手动抓取与目标化管理。
- `SubredditsPage`：升级为“监控目标”页面（跨平台）。
- `DashboardPage`：新增跨平台 KPI（targets/source_items）。
- `AppLayout`：导航文案升级为平台无关。

## Migration Strategy

### Phase A (Now)

- 新老模型并行，API 兼容保留。
- 新功能全部基于 `sources/*`。

### Phase B (Recommended)

- 将前端剩余 legacy 调用迁移至 `sources/*`。
- 对历史 `posts/comments` 做一次性回填到 `source_items/source_comments`（可选）。

### Phase C (Optional)

- 下线 legacy `subreddits/posts/comments`，彻底统一到 source 模型。

## Adding a New Source (Playbook)

1. 新增 `backend/app/services/sources/<new_source>.py` 实现 `SourceAdapter`。
2. 在 `source_registry` 注册。
3. 若需要，扩展前端目标类型枚举与抓取表单。
4. 无需改核心入库/调度/标签/统计逻辑。

## Notes

- HN 的 feed 与 story 为多对多语义，统一模型天然支持，无需单独 feed/story 绑定表。
- 调度间隔单位统一为“分钟”，避免跨模块语义冲突。
- 当前已保证兼容运行，但建议逐步减少对 legacy 表的依赖。

