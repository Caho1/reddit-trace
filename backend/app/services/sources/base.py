from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class SourceAdapter(ABC):
    source: str
    display_name: str

    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def normalize_target_key(self, target_type: str, target_key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def fetch_target_items(
        self,
        *,
        target_type: str,
        target_key: str,
        limit: int,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_item_comments(
        self,
        *,
        item_external_id: str,
        item_url: Optional[str],
        limit: int,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def close(self):
        return None


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        from datetime import timezone

        return dt.replace(tzinfo=timezone.utc)
    return dt

