"""OpenAI LLM 实现"""

import os
import json
from typing import List

from openai import AsyncOpenAI

from app.config import settings
from app.llm.base import BaseLLM


class OpenAILLM(BaseLLM):
    """OpenAI LLM 服务实现"""

    def __init__(self):
        # 设置代理环境变量
        if settings.http_proxy:
            os.environ["HTTP_PROXY"] = settings.http_proxy
        if settings.https_proxy:
            os.environ["HTTPS_PROXY"] = settings.https_proxy

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.screening_model = settings.default_screening_model
        self.analysis_model = settings.default_analysis_model

    async def analyze_comment(self, content: str) -> dict:
        """分析评论内容"""
        system_prompt = """你是一个专业的评论分析助手。请分析给定的评论内容，返回JSON格式的分析结果。
分析结果应包含以下字段：
- sentiment: 情感倾向 (positive/negative/neutral)
- sentiment_score: 情感分数 (-1到1之间)
- topics: 主题列表
- keywords: 关键词列表
- summary: 简短摘要
- language: 检测到的语言"""

        response = await self.client.chat.completions.create(
            model=self.analysis_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析以下评论：\n\n{content}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        result = json.loads(response.choices[0].message.content)
        return result

    async def screen_comments(self, comments: List[str]) -> List[bool]:
        """批量筛选评论"""
        if not comments:
            return []

        system_prompt = """你是一个评论筛选助手。请判断每条评论是否有价值（包含有意义的观点、信息或讨论）。
返回JSON格式，包含一个 "results" 数组，数组中每个元素为 true（有价值）或 false（无价值）。
无价值的评论包括：垃圾信息、纯表情、无意义的短回复、广告等。"""

        comments_text = "\n".join(
            [f"{i+1}. {c}" for i, c in enumerate(comments)]
        )

        response = await self.client.chat.completions.create(
            model=self.screening_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请筛选以下评论：\n\n{comments_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("results", [True] * len(comments))

    async def translate(self, text: str) -> str:
        """翻译文本到中文"""
        if not text:
            return ""

        response = await self.client.chat.completions.create(
            model=self.screening_model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的翻译助手。请将用户提供的文本翻译成中文。只返回翻译结果，不要添加任何解释。"
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()
