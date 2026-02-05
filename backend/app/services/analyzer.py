from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import OpenAILLM, ClaudeLLM
from app.config import settings
from app.models.comment import Comment
from app.models.analysis import Analysis


class AnalyzerService:
    def __init__(self):
        self.screening_llm = self._get_llm(settings.default_screening_model)
        self.analysis_llm = self._get_llm(settings.default_analysis_model)

    def _get_llm(self, model: str):
        if "gpt" in model.lower():
            return OpenAILLM(model=model)
        elif "claude" in model.lower():
            return ClaudeLLM(model=model)
        return OpenAILLM(model=model)

    async def screen_comments(self, comments: List[Comment]) -> List[bool]:
        """阶段1: 批量筛选有价值的评论"""
        contents = [c.content for c in comments]
        return await self.screening_llm.screen_comments(contents)

    async def analyze_comment(self, comment: Comment, db: AsyncSession) -> Analysis:
        """阶段2: 深度分析单条评论"""
        result = await self.analysis_llm.analyze_comment(comment.content)

        analysis = Analysis(
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

    async def translate_comment(self, comment: Comment, db: AsyncSession):
        """翻译评论内容"""
        if comment.content and not comment.content_zh:
            comment.content_zh = await self.analysis_llm.translate(comment.content)
            await db.commit()


analyzer = AnalyzerService()
