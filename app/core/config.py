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
    llm_provider: str = Field(default="aicredits", alias="LLM_PROVIDER")
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
    composio_base_url: str = Field(default="https://backend.composio.dev/api/v3.1", alias="COMPOSIO_BASE_URL")
    composio_callback_url: str | None = Field(default=None, alias="COMPOSIO_CALLBACK_URL")
    composio_gmail_auth_config_id: str | None = Field(default=None, alias="COMPOSIO_GMAIL_AUTH_CONFIG_ID")
    composio_notion_auth_config_id: str | None = Field(default=None, alias="COMPOSIO_NOTION_AUTH_CONFIG_ID")
    composio_github_auth_config_id: str | None = Field(default=None, alias="COMPOSIO_GITHUB_AUTH_CONFIG_ID")
    composio_gmail_fetch_tool_slug: str = Field(default="GMAIL_FETCH_EMAILS", alias="COMPOSIO_GMAIL_FETCH_TOOL_SLUG")
    composio_github_search_tool_slug: str = Field(default="GITHUB_SEARCH_ISSUES", alias="COMPOSIO_GITHUB_SEARCH_TOOL_SLUG")
    composio_notion_create_page_tool_slug: str = Field(
        default="NOTION_CREATE_PAGE",
        alias="COMPOSIO_NOTION_CREATE_PAGE_TOOL_SLUG",
    )
    serper_api_key: str | None = Field(default=None, alias="SERPER_API_KEY")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    enable_tavily_fallback: bool = Field(default=False, alias="ENABLE_TAVILY_FALLBACK")
    cors_origins_raw: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        if self.app_env == "production":
            return None
        return r"^http://(localhost|127\.0\.0\.1):[0-9]+$"

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
