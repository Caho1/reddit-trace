from __future__ import annotations

from typing import Dict

from app.services.sources.base import SourceAdapter
from app.services.sources.hackernews import HackerNewsAdapter
from app.services.sources.reddit import RedditAdapter


class SourceRegistry:
    """多平台适配器注册中心。

    统一管理适配器实例生命周期，并提供按 ``source`` 查询适配器的入口。
    """

    def __init__(self):
        self._adapters: Dict[str, SourceAdapter] = {
            "reddit": RedditAdapter(),
            "hackernews": HackerNewsAdapter(),
        }

    def get(self, source: str) -> SourceAdapter:
        """按来源键获取适配器实例。

        参数：
            source: 平台标识，例如 ``reddit``、``hackernews``。

        返回：
            SourceAdapter: 已注册的适配器实例。

        异常：
            ValueError: 当 ``source`` 未注册时抛出。
        """
        key = (source or "").strip().lower()
        adapter = self._adapters.get(key)
        if not adapter:
            raise ValueError(f"Unsupported source: {source}")
        return adapter

    def all(self) -> Dict[str, SourceAdapter]:
        """返回适配器映射的浅拷贝。"""
        return dict(self._adapters)

    async def close_all(self):
        """关闭全部适配器资源（如 HTTP 客户端）。"""
        for adapter in self._adapters.values():
            await adapter.close()


source_registry = SourceRegistry()
