from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PRODUCTION_EMBEDDING_MODEL = "BAAI/bge-m3@dr-ai-mainland-v1"
PRODUCTION_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3@dr-ai-mainland-medical-v1"
STAGING_GTE_EMBEDDING_MODEL = "Alibaba-NLP/gte-multilingual-base@9bbca17d9273"
STAGING_GTE_RERANKER_MODEL = "Alibaba-NLP/gte-multilingual-reranker-base@8215cf04918b"


class Settings(BaseSettings):
    app_name: str = "Dr. AI API"
    environment: Literal["local", "test", "staging", "production"] = "local"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"
    deployment_source_revision: str = "unrecorded"
    deployment_image_digest: str = "unrecorded"
    deployment_web_sha256: str = "unrecorded"
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
    deepseek_timeout_seconds: float = 15.0
    imaging_storage_backend: Literal["local", "tencent_cos"] = "local"
    imaging_local_storage_root: str = "/tmp/dr_ai_synthetic_imaging"
    imaging_tencent_cos_bucket: str | None = None
    imaging_tencent_cos_region: str | None = None
    notification_external_delivery_enabled: bool = False
    notification_apns_team_id: str | None = None
    notification_apns_key_id: str | None = None
    notification_apns_bundle_id: str | None = None
    notification_apns_private_key: SecretStr | None = None
    notification_emas_app_key: str | None = None
    notification_emas_app_secret: SecretStr | None = None
    notification_emas_android_package: str | None = None
    notification_emas_oem_approvals_verified: bool = False
    notification_web_push_vapid_public_key: str | None = None
    notification_web_push_vapid_private_key: SecretStr | None = None
    notification_web_push_subject: str | None = None
    notification_worker_enabled: bool = False
    chatbot_provider: Literal["deepseek"] = "deepseek"
    chatbot_purpose_enabled: bool = False
    chatbot_kill_switch: bool = True
    chatbot_release_governance_bypass_for_tests: bool = False
    expected_care_candidate_enabled: bool = False
    expected_care_provider: str = "deepseek"
    expected_care_model: str = "deepseek-v4-flash"
    expected_care_timeout_seconds: float = Field(default=15.0, ge=0.1, le=30.0)
    expected_care_max_attempts: int = Field(default=2, ge=1, le=2)
    expected_care_max_output_tokens: int = Field(default=1200, ge=100, le=2000)
    expected_care_max_cost_microunits: int = Field(default=2500, ge=1, le=10000)
    expected_care_explanation_enabled: bool = False
    expected_care_explanation_provider: Literal["deepseek"] = "deepseek"
    expected_care_explanation_model: str = "deepseek-v4-flash"
    expected_care_explanation_timeout_seconds: float = Field(default=8.0, ge=0.1, le=30.0)
    expected_care_explanation_max_attempts: int = Field(default=2, ge=1, le=2)
    expected_care_explanation_max_output_tokens: int = Field(default=1200, ge=400, le=2000)
    expected_care_explanation_kill_switch: bool = True
    clinical_event_intelligence_primary_enabled: bool = False
    clinical_event_intelligence_primary_kill_switch: bool = True
    clinical_event_intelligence_primary_provider: Literal["deepseek"] = "deepseek"
    clinical_event_intelligence_primary_model: str = "deepseek-v4-pro"
    clinical_event_intelligence_primary_timeout_seconds: float = Field(
        default=20.0, ge=0.1, le=60.0
    )
    clinical_event_intelligence_primary_max_attempts: int = Field(default=2, ge=1, le=2)
    clinical_event_intelligence_primary_max_output_tokens: int = Field(
        default=4000, ge=500, le=8000
    )
    clinical_event_intelligence_primary_max_cost_microunits: int = Field(
        default=20000, ge=1, le=1_000_000
    )
    clinical_event_intelligence_primary_input_price_per_million_usd: float = Field(
        default=0.435, ge=0.0
    )
    clinical_event_intelligence_primary_output_price_per_million_usd: float = Field(
        default=0.87, ge=0.0
    )
    clinical_event_intelligence_critic_enabled: bool = False
    clinical_event_intelligence_critic_kill_switch: bool = True
    clinical_event_intelligence_critic_provider: Literal["deepseek"] = "deepseek"
    clinical_event_intelligence_critic_model: str = "deepseek-v4-pro"
    clinical_event_intelligence_critic_timeout_seconds: float = Field(default=20.0, ge=0.1, le=60.0)
    clinical_event_intelligence_critic_max_output_tokens: int = Field(default=1800, ge=300, le=4000)
    clinical_event_intelligence_critic_max_cost_microunits: int = Field(
        default=10000, ge=1, le=1_000_000
    )
    clinical_event_intelligence_critic_input_price_per_million_usd: float = Field(
        default=0.435, ge=0.0
    )
    clinical_event_intelligence_critic_output_price_per_million_usd: float = Field(
        default=0.87, ge=0.0
    )
    clinical_event_intelligence_explanation_enabled: bool = False
    clinical_event_intelligence_explanation_kill_switch: bool = True
    clinical_event_intelligence_explanation_provider: Literal["deepseek"] = "deepseek"
    clinical_event_intelligence_explanation_model: str = "deepseek-v4-flash"
    clinical_event_intelligence_explanation_timeout_seconds: float = Field(
        default=8.0, ge=0.1, le=30.0
    )
    clinical_event_intelligence_explanation_max_attempts: int = Field(default=2, ge=1, le=2)
    clinical_event_intelligence_explanation_max_output_tokens: int = Field(
        default=1400, ge=300, le=3000
    )
    clinical_event_intelligence_explanation_max_cost_microunits: int = Field(
        default=5000, ge=1, le=1_000_000
    )
    clinical_event_intelligence_explanation_input_price_per_million_usd: float = Field(
        default=0.14, ge=0.0
    )
    clinical_event_intelligence_explanation_output_price_per_million_usd: float = Field(
        default=0.28, ge=0.0
    )
    chatbot_grounded_generation_enabled: bool = True
    chatbot_general_model_knowledge_enabled: bool = True
    chatbot_grounded_answer_schema_version: str = "grounded-answer-v2-2026-07-24"
    chatbot_general_answer_schema_version: str = "general-knowledge-v1-2026-07-24"
    chatbot_semantic_routing_purpose_enabled: bool = False
    chatbot_semantic_routing_kill_switch: bool = True
    chatbot_semantic_routing_schema_version: str = "patient-semantic-route-v1-2026-08-13"
    chatbot_semantic_router_max_latency_ms: int = Field(default=2500, ge=100, le=10000)
    chatbot_semantic_router_max_cost_microunits: int = Field(default=1000, ge=1, le=100000)
    chatbot_differential_planning_purpose_enabled: bool = False
    chatbot_differential_planning_kill_switch: bool = True
    chatbot_differential_planning_schema_version: str = (
        "patient-differential-plan-v1-2026-08-13"
    )
    chatbot_differential_planning_max_latency_ms: int = Field(default=8000, ge=100, le=10000)
    chatbot_differential_planning_max_cost_microunits: int = Field(
        default=1600, ge=1, le=100000
    )
    retrieval_rescue_enabled: bool = True
    retrieval_rescue_max_latency_ms: int = Field(default=2500, ge=100, le=10000)
    retrieval_rescue_max_cost_microunits: int = Field(default=1000, ge=1, le=100000)
    retrieval_rescue_weak_score_threshold: float = Field(default=0.18, ge=0.0, le=1.0)
    deepseek_input_price_per_million_usd: float = Field(default=0.14, ge=0.0)
    deepseek_output_price_per_million_usd: float = Field(default=0.28, ge=0.0)
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
    knowledge_reranker_backend: Literal["local_baseline", "http_service"] = "local_baseline"
    knowledge_reranker_service_url: str | None = None
    knowledge_reranker_model: str = "dr-ai-policy-reranker-v5-central-clinical-concepts"
    knowledge_reranker_timeout_seconds: float = 3.0
    knowledge_reranker_max_candidates: int = Field(default=30, ge=1, le=30)
    knowledge_model_service_data_region: Literal["hong_kong", "mainland_china"] = "mainland_china"

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
        if self.knowledge_reranker_backend == "http_service" and not (
            self.knowledge_reranker_service_url
            and self.knowledge_reranker_service_url.startswith(("http://", "https://"))
        ):
            raise ValueError("HTTP knowledge reranking requires a service URL")
        if self.retrieval_rescue_enabled and self.retrieval_rescue_max_cost_microunits <= 0:
            raise ValueError("Retrieval rescue requires a positive per-request cost budget")
        if self.imaging_storage_backend == "tencent_cos" and (
            not self.imaging_tencent_cos_bucket or not self.imaging_tencent_cos_region
        ):
            raise ValueError(
                "Tencent COS imaging requires an explicitly configured bucket and region"
            )
        if self.environment == "production" and (
            self.knowledge_embedding_backend != "http_service"
            or self.knowledge_reranker_backend != "http_service"
            or self.knowledge_embedding_model != PRODUCTION_EMBEDDING_MODEL
            or self.knowledge_reranker_model != PRODUCTION_RERANKER_MODEL
        ):
            raise ValueError(
                "Production retrieval requires the approved Mainland-China embedding "
                "and reranker services"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
