from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ScrapMaster Unified API"
    environment: str = "development"
    database_url: str = "sqlite:///./scrapmaster.db"
    api_access_token: SecretStr | None = None
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "test", "staging", "production"}
        if value not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {sorted(allowed)}")
        return value

    def validate_runtime(self) -> None:
        if self.environment == "production":
            if not self.api_access_token or len(self.api_access_token.get_secret_value()) < 32:
                raise ValueError("API_ACCESS_TOKEN must contain at least 32 characters in production")
            if self.database_url.startswith("sqlite"):
                raise ValueError("Production requires PostgreSQL; SQLite is for local/test use only")


@lru_cache
def get_settings() -> Settings:
    return Settings()
