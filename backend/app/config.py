from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 数据库
    database_url: str = "postgresql://user:password@localhost:5432/reddit_trace"
    auto_create_tables: bool = False

    # 代理配置
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None

    # Reddit OAuth（可选，推荐）
    # 创建应用：https://www.reddit.com/prefs/apps
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "reddit-trace/0.1"

    # OpenAI (兼容格式)
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.apimart.ai/v1"

    # Claude
    anthropic_api_key: Optional[str] = None

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # 默认模型配置
    default_llm_provider: str = "openai"
    default_screening_model: str = "gemini-2.0-flash"
    default_analysis_model: str = "gemini-2.5-pro-preview"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
