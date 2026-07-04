from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Dr. AI API"
    environment: Literal["local", "test", "staging", "production"] = "local"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://localhost/dr_ai"
    jwt_secret: SecretStr = SecretStr(
        "local-development-only-change-before-staging-32-characters"
    )
    jwt_issuer: str = "dr-ai-api"
    jwt_audience: str = "dr-ai-app"
    access_token_minutes: int = 10
    refresh_token_days: int = 14
    doctor_invite_code: SecretStr | None = None
    patient_invite_code: SecretStr | None = None
    seed_doctor_password: SecretStr | None = None
    seed_patient_password: SecretStr | None = None
    seed_unrelated_patient_password: SecretStr | None = None
    cors_allowed_origins: list[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DR_AI_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def reject_local_secret_outside_local_environments(self) -> "Settings":
        secret = self.jwt_secret.get_secret_value()
        if self.environment in {"staging", "production"} and secret.startswith(
            "local-development-only"
        ):
            raise ValueError("DR_AI_JWT_SECRET must be set for staging and production")
        if len(secret) < 32:
            raise ValueError("DR_AI_JWT_SECRET must contain at least 32 characters")
        if self.environment in {"staging", "production"} and "*" in (
            origin.strip() for origin in self.cors_allowed_origins
        ):
            raise ValueError(
                "DR_AI_CORS_ALLOWED_ORIGINS cannot contain * in staging or production"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
