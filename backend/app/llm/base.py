"""LLM 抽象基类定义"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseLLM(ABC):
    """LLM 服务抽象基类"""

    @abstractmethod
    async def analyze_comment(self, content: str) -> dict:
        """
        分析评论内容

        Args:
            content: 评论文本内容

        Returns:
            dict: 分析结果，包含情感、主题、关键词等信息
        """
        pass

    @abstractmethod
    async def screen_comments(self, comments: List[str]) -> List[bool]:
        """
        批量筛选评论

        Args:
            comments: 评论文本列表

        Returns:
            List[bool]: 每条评论是否通过筛选
        """
        pass

    @abstractmethod
    async def translate(self, text: str) -> str:
        """
        翻译文本到中文

        Args:
            text: 待翻译的文本

        Returns:
            str: 翻译后的中文文本
        """
        pass
