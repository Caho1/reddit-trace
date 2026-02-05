"""Claude LLM 实现"""

import os
import json
from typing import List

from anthropic import AsyncAnthropic

from app.config import settings
from app.llm.base import BaseLLM


class ClaudeLLM(BaseLLM):
    """Claude LLM 服务实现"""

    def __init__(self):
        # 设置代理环境变量
        if settings.http_proxy:
            os.environ["HTTP_PROXY"] = settings.http_proxy
        if settings.https_proxy:
            os.environ["HTTPS_PROXY"] = settings.https_proxy

        self.client = AsyncAnthropic(
            api_key=settings.anthropic_api_key,
        )
        self.model = "claude-3-sonnet-20240229"

    async def analyze_comment(self, content: str) -> dict:
        """分析评论内容"""
        system_prompt = """你是一个专业的评论分析助手。请分析给定的评论内容，返回JSON格式的分析结果。
分析结果应包含以下字段：
- sentiment: 情感倾向 (positive/negative/neutral)
- sentiment_score: 情感分数 (-1到1之间)
- topics: 主题列表
- keywords: 关键词列表
- summary: 简短摘要
- language: 检测到的语言

只返回JSON，不要添加其他内容。"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"请分析以下评论：\n\n{content}"}
            ],
        )

        result = json.loads(response.content[0].text)
        return result

    async def screen_comments(self, comments: List[str]) -> List[bool]:
        """批量筛选评论"""
        if not comments:
            return []

        system_prompt = """你是一个评论筛选助手。请判断每条评论是否有价值。
返回JSON格式，包含一个 "results" 数组，每个元素为 true 或 false。
无价值的评论包括：垃圾信息、纯表情、无意义的短回复、广告等。
只返回JSON，不要添加其他内容。"""

        comments_text = "\n".join(
            [f"{i+1}. {c}" for i, c in enumerate(comments)]
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"请筛选以下评论：\n\n{comments_text}"}
            ],
        )

        result = json.loads(response.content[0].text)
        return result.get("results", [True] * len(comments))

    async def translate(self, text: str) -> str:
        """翻译文本到中文"""
        if not text:
            return ""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system="你是一个专业的翻译助手。请将用户提供的文本翻译成中文。只返回翻译结果，不要添加任何解释。",
            messages=[
                {"role": "user", "content": text}
            ],
        )

        return response.content[0].text.strip()
