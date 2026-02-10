"""Configuration for TeleOps."""

import logging
import sys
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core
    app_name: str = "teleops"
    environment: str = "local"
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"

    # Database
    database_url: str = "sqlite:///./teleops.db"

    # LLM provider selection
    # local_telellm | hosted_telellm | gemini
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.0-flash"
    llm_timeout_seconds: float = 60.0

    # OpenAI-compatible endpoint for local/hosted Tele-LLM
    llm_base_url: str = "http://localhost:8001/v1"
    llm_api_key: str | None = None

    # Gemini
    gemini_api_key: str | None = None
    gemini_timeout_seconds: float = 120.0

    # RAG
    rag_corpus_dir: str = "./docs/rag_corpus"
    rag_index_dir: str = "./storage/rag_index"
    rag_top_k: int = 6

    # Integrations
    integrations_fixtures_dir: str = "./docs/integrations/fixtures"
    integrations_log_path: str = "./storage/integration_events.jsonl"

    # Metrics artifacts
    test_results_path: str = "./storage/test_results.json"
    evaluation_results_path: str = "./storage/evaluation_results.json"

    # Audit log
    audit_log_path: str = "./storage/audit_log.jsonl"

    # Access control (optional)
    api_token: str | None = None
    admin_token: str | None = None
    metrics_token: str | None = None
    require_tenant_id: bool = False

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:8501", "http://localhost:3000"])

    # Log rotation (integration + audit)
    integration_log_max_bytes: int = 5_000_000
    integration_log_backup_count: int = 3
    audit_log_max_bytes: int = 5_000_000
    audit_log_backup_count: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


def setup_logging() -> logging.Logger:
    """Configure structured logging for TeleOps.

    Returns a logger instance configured based on environment settings.
    JSON format is used for production, text format for local development.
    """
    logger = logging.getLogger("teleops")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.log_format == "json":
        # JSON format for production/observability
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        # Human-readable format for local development
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Initialize logger on module load
logger = setup_logging()
