from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 数据库
    database_url: str = "postgresql://user:password@localhost:5432/reddit_trace"

    # 代理配置
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"

    # Claude
    anthropic_api_key: Optional[str] = None

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # 默认模型配置
    default_llm_provider: str = "openai"
    default_screening_model: str = "gpt-3.5-turbo"
    default_analysis_model: str = "gpt-4"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
