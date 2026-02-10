from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import OpenAILLM, ClaudeLLM
from app.config import settings
from app.models.source_comments import SourceComment
from app.models.source_comments import SourceAnalysis


class AnalyzerService:
    """基于 LLM 的评论分析服务。

    采用两阶段流程：先筛选高价值评论，再进行深度分析。
    """

    def __init__(self):
        """根据配置初始化筛选模型与分析模型。"""
        self.screening_llm = self._get_llm(settings.default_screening_model)
        self.analysis_llm = self._get_llm(settings.default_analysis_model)

    def _get_llm(self, model: str):
        """根据模型名约定选择具体 LLM 客户端。

        参数：
            model: 模型标识字符串。

        返回：
            OpenAILLM | ClaudeLLM: LLM 客户端实例。
        """
        if "gpt" in model.lower():
            return OpenAILLM(model=model)
        elif "claude" in model.lower():
            return ClaudeLLM(model=model)
        return OpenAILLM(model=model)

    async def screen_comments(self, comments: List[SourceComment]) -> List[bool]:
        """阶段一：批量筛选评论价值。

        参数：
            comments: 待筛选评论列表。

        返回：
            List[bool]: 与输入评论一一对应的筛选结果。
        """
        contents = [c.content for c in comments]
        return await self.screening_llm.screen_comments(contents)

    async def analyze_comment(self, comment: SourceComment, db: AsyncSession) -> SourceAnalysis:
        """阶段二：深度分析单条评论并入库。

        参数：
            comment: 待分析评论。
            db: 异步数据库会话。

        返回：
            SourceAnalysis: 持久化后的分析结果。
        """
        result = await self.analysis_llm.analyze_comment(comment.content)

        analysis = SourceAnalysis(
            comment_id=comment.id,
            pain_points=result.get("pain_points", []),
            user_needs=result.get("user_needs", []),
            opportunities=result.get("opportunities", []),
            model_used=settings.default_analysis_model,
            is_valuable=1
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        return analysis

    async def translate_comment(self, comment: SourceComment, db: AsyncSession):
        """在缺失中文内容时翻译评论。

        参数：
            comment: 评论实体。
            db: 异步数据库会话。
        """
        if comment.content and not comment.content_zh:
            comment.content_zh = await self.analysis_llm.translate(comment.content)
            await db.commit()


analyzer = AnalyzerService()
