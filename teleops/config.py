"""Configuration for TeleOps."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core
    app_name: str = "teleops"
    environment: str = "local"

    # Database
    database_url: str = "sqlite:///./teleops.db"

    # LLM provider selection
    # local_telellm | hosted_telellm | gemini
    llm_provider: str = "local_telellm"
    llm_model: str = "tele-llm-3b"

    # OpenAI-compatible endpoint for local/hosted Tele-LLM
    llm_base_url: str = "http://localhost:8001/v1"
    llm_api_key: str | None = None

    # Gemini
    gemini_api_key: str | None = None

    # RAG
    rag_corpus_dir: str = "./docs/rag_corpus"
    rag_index_dir: str = "./storage/rag_index"
    rag_top_k: int = 4

    # Integrations
    integrations_fixtures_dir: str = "./docs/integrations/fixtures"
    integrations_log_path: str = "./storage/integration_events.jsonl"

    # Metrics artifacts
    test_results_path: str = "./storage/test_results.json"
    evaluation_results_path: str = "./storage/evaluation_results.json"

    # Access control (optional)
    api_token: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
