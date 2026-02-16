import pytest

from teleops.config import Settings


def _set_required_env(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", "test-api")
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin")
    monkeypatch.setenv("METRICS_TOKEN", "test-metrics")


def test_production_requires_tokens(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    for key in ["API_TOKEN", "ADMIN_TOKEN", "METRICS_TOKEN"]:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValueError) as excinfo:
        Settings(_env_file=None)

    message = str(excinfo.value)
    assert "API_TOKEN" in message
    assert "ADMIN_TOKEN" in message
    assert "METRICS_TOKEN" in message


def test_production_requires_tenant_id_when_enforced(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    _set_required_env(monkeypatch)
    monkeypatch.setenv("REQUIRE_TENANT_ID", "true")
    monkeypatch.delenv("TELEOPS_TENANT_ID", raising=False)

    with pytest.raises(ValueError) as excinfo:
        Settings(_env_file=None)

    assert "TELEOPS_TENANT_ID" in str(excinfo.value)


def test_production_allows_with_tenant_id(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    _set_required_env(monkeypatch)
    monkeypatch.setenv("REQUIRE_TENANT_ID", "true")
    monkeypatch.setenv("TELEOPS_TENANT_ID", "demo-tenant")

    settings = Settings(_env_file=None)
    assert settings.environment == "production"
    assert settings.teleops_tenant_id == "demo-tenant"
