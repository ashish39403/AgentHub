from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="AgentHub", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    database_url: str = Field(
        default="postgresql+asyncpg://agenthub:agenthub@localhost:5433/agenthub",
        alias="DATABASE_URL",
    )
    jwt_secret_key: str = Field(
        default="change-me-to-a-random-64-character-secret-before-production",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=15, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=30, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    agent_max_iterations: int = Field(default=4, alias="AGENT_MAX_ITERATIONS")
    llm_model_default: str = Field(default="google/gemini-2.5-flash", alias="LLM_MODEL_DEFAULT")
    llm_model_fast: str = Field(default="google/gemini-2.5-flash", alias="LLM_MODEL_FAST")
    llm_model_smart: str = Field(default="deepseek/deepseek-v4-pro", alias="LLM_MODEL_SMART")
    llm_model_reasoning: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b", alias="LLM_MODEL_REASONING")
    llm_model_cheap: str = Field(default="openai/gpt-3.5-turbo-0613", alias="LLM_MODEL_CHEAP")
    llm_model_experimental: str = Field(default="gpt-5-mini", alias="LLM_MODEL_EXPERIMENTAL")
    aicredits_base_url: str | None = Field(default=None, alias="AICREDITS_BASE_URL")
    aicredits_api_key: str | None = Field(default=None, alias="AICREDITS_API_KEY")
    composio_api_key: str | None = Field(default=None, alias="COMPOSIO_API_KEY")
    serpapi_api_key: str | None = Field(default=None, alias="SERPAPI_API_KEY")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    cors_origins_raw: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def llm_models(self) -> dict[str, str]:
        return {
            "default": self.llm_model_default,
            "fast": self.llm_model_fast,
            "smart": self.llm_model_smart,
            "reasoning": self.llm_model_reasoning,
            "cheap": self.llm_model_cheap,
            "experimental": self.llm_model_experimental,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
