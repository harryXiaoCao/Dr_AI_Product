from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Dr. AI API"
    environment: Literal["local", "test", "staging", "production"] = "local"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://localhost/dr_ai"
    jwt_secret: SecretStr = SecretStr("local-development-only-change-before-staging-32-characters")
    jwt_issuer: str = "dr-ai-api"
    jwt_audience: str = "dr-ai-app"
    access_token_minutes: int = 10
    refresh_token_days: int = 14
    seed_doctor_password: SecretStr | None = None
    seed_patient_password: SecretStr | None = None
    seed_unrelated_patient_password: SecretStr | None = None
    cors_allowed_origins: list[str] = []
    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: str = "https://api.deepseek.com/chat/completions"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_timeout_seconds: float = 8.0
    chat_rate_limit_messages: int = 4
    chat_rate_limit_window_seconds: int = 60
    chatbot_data_mode: Literal["synthetic_only", "approved_real_context"] = "synthetic_only"
    chatbot_external_provider_real_context_enabled: bool = False
    chatbot_external_provider_data_region: Literal["mainland_china"] = "mainland_china"
    chatbot_external_provider_allowed_context_fields: list[str] = Field(default_factory=list)
    chatbot_external_provider_no_training_contract_verified: bool = False
    chatbot_external_provider_no_retention_contract_verified: bool = False
    chatbot_external_provider_privacy_review_id: str | None = None
    chatbot_external_provider_legal_review_id: str | None = None
    chatbot_external_provider_product_approval_id: str | None = None
    knowledge_embedding_backend: Literal["local_baseline", "http_service"] = "local_baseline"
    knowledge_embedding_service_url: str | None = None
    knowledge_embedding_model: str = "dr-ai-hashed-multilingual-v1"
    knowledge_embedding_timeout_seconds: float = 3.0

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
            raise ValueError("DR_AI_CORS_ALLOWED_ORIGINS cannot contain * in staging or production")
        real_context_approvals = (
            self.chatbot_data_mode == "approved_real_context",
            self.chatbot_external_provider_real_context_enabled,
            bool(self.chatbot_external_provider_allowed_context_fields),
            self.chatbot_external_provider_no_training_contract_verified,
            self.chatbot_external_provider_no_retention_contract_verified,
            bool(self.chatbot_external_provider_privacy_review_id),
            bool(self.chatbot_external_provider_legal_review_id),
            bool(self.chatbot_external_provider_product_approval_id),
        )
        if any(real_context_approvals) and not all(real_context_approvals):
            raise ValueError("External-provider real patient context requires every approval gate")
        if self.knowledge_embedding_backend == "http_service" and not (
            self.knowledge_embedding_service_url
            and self.knowledge_embedding_service_url.startswith(("http://", "https://"))
        ):
            raise ValueError("HTTP knowledge embeddings require a service URL")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
