import pytest

from teleops.config import Settings


def _set_required_env(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", "test-api")
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin")
    monkeypatch.setenv("METRICS_TOKEN", "test-metrics")


def test_production_warns_on_missing_tokens(monkeypatch, capsys):
    """App starts in production without tokens but prints a warning."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    for key in ["API_TOKEN", "ADMIN_TOKEN", "METRICS_TOKEN"]:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    # Tokens remain None (open access)
    assert settings.api_token is None
    assert settings.admin_token is None
    assert settings.metrics_token is None

    # Warning was printed to stderr
    captured = capsys.readouterr()
    assert "Missing security tokens for production" in captured.err
    assert "API_TOKEN" in captured.err
    assert "ADMIN_TOKEN" in captured.err
    assert "METRICS_TOKEN" in captured.err


def test_production_warns_on_missing_tenant_id(monkeypatch, capsys):
    """Warns about TELEOPS_TENANT_ID when require_tenant_id is set."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    _set_required_env(monkeypatch)
    monkeypatch.setenv("REQUIRE_TENANT_ID", "true")
    monkeypatch.delenv("TELEOPS_TENANT_ID", raising=False)

    settings = Settings(_env_file=None)

    assert settings.teleops_tenant_id is None
    captured = capsys.readouterr()
    assert "TELEOPS_TENANT_ID" in captured.err


def test_production_allows_with_tenant_id(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    _set_required_env(monkeypatch)
    monkeypatch.setenv("REQUIRE_TENANT_ID", "true")
    monkeypatch.setenv("TELEOPS_TENANT_ID", "demo-tenant")

    settings = Settings(_env_file=None)
    assert settings.environment == "production"
    assert settings.teleops_tenant_id == "demo-tenant"


def test_production_no_warning_when_tokens_set(monkeypatch, capsys):
    """No warning when all tokens are provided."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    _set_required_env(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.api_token == "test-api"
    assert settings.admin_token == "test-admin"
    assert settings.metrics_token == "test-metrics"

    captured = capsys.readouterr()
    assert "Missing security tokens" not in captured.err
