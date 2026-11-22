"""Offline tests for strict local API settings."""

from datetime import UTC, datetime, timedelta, tzinfo
from pathlib import Path

import pytest
from pydantic import SecretStr

from nowa_customer_intelligence.api import configuration
from nowa_customer_intelligence.api.configuration import ApiConfiguration, ConfigurationError

_NOW = datetime(2026, 11, 21, 12, tzinfo=UTC)
_SECRET = "fixture_secret_for_validation_123456"


class FixedDateTime:
    fromisoformat = staticmethod(datetime.fromisoformat)

    @classmethod
    def now(cls, tz: tzinfo | None = None) -> datetime:
        return _NOW


@pytest.fixture
def demo_environment(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    monkeypatch.setattr(configuration, "datetime", FixedDateTime)
    return {
        "NCI_API_MODE": "loopback",
        "NCI_API_BUNDLE_ROOT": "/fixtures/research",
        "NCI_API_RELEASE_SHA256": "a" * 64,
        "NCI_API_BEARER_SECRET": _SECRET,
        "NCI_API_BEARER_EXPIRES_AT": "2026-11-21T13:00:00Z",
    }


def test_default_in_process_is_explicitly_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NCI_API_MODE", "loopback")
    settings = ApiConfiguration()
    assert settings.mode == "in-process"
    assert settings.log_level == "INFO"
    assert settings.bind_host is settings.bind_port is settings.bearer_secret is None
    assert settings.bundle_root is settings.release_sha256 is None
    assert ApiConfiguration.from_environment({"UNRELATED": "value"}) == settings


def test_loopback_defaults_and_secret_redaction(demo_environment: dict[str, str]) -> None:
    settings = ApiConfiguration.from_environment(demo_environment)
    assert settings.mode == "loopback"
    assert settings.bind_host == "127.0.0.1"
    assert settings.bind_port == 8000
    assert settings.bundle_root == Path("/fixtures/research")
    assert settings.bearer_expires_at == _NOW + timedelta(hours=1)
    assert settings.bearer_secret == SecretStr(_SECRET)
    assert "bearer_secret" not in settings.model_dump()
    assert _SECRET not in str(settings) + repr(settings) + settings.model_dump_json()


def test_loopback_accepts_explicit_ipv6_and_port(demo_environment: dict[str, str]) -> None:
    settings = ApiConfiguration.from_environment(
        demo_environment | {"NCI_API_BIND_HOST": "::1", "NCI_API_BIND_PORT": "8042"}
    )
    assert (settings.bind_host, settings.bind_port) == ("::1", 8042)


@pytest.mark.parametrize(
    ("setting", "value"),
    [
        ("MODE", "production"),
        ("BEARER_SECRET", ""),
        ("BEARER_SECRET", "invalid secret"),
        ("BEARER_EXPIRES_AT", "2026-11-21T19:00:00"),
        ("BEARER_EXPIRES_AT", "2026-11-31T19:00:00Z"),
        ("BEARER_EXPIRES_AT", "2026-11-21T12:00:00Z"),
        ("BEARER_EXPIRES_AT", "2026-11-21T20:00:01Z"),
        ("BIND_HOST", "0.0.0.0"),
        ("BIND_HOST", "::"),
        ("BIND_HOST", "localhost"),
        ("BIND_PORT", "080"),
        ("BIND_PORT", "65536"),
        ("BIND_PORT", "80.0"),
        ("RELEASE_SHA256", "Z" * 64),
        ("BUNDLE_ROOT", "relative/private"),
        ("BUNDLE_ROOT", "/fixtures/../private"),
        ("LOG_LEVEL", "DEBUG"),
        ("UNEXPECTED_SETTING", "private-value"),
    ],
)
def test_invalid_settings_fail_closed_without_exposing_input(
    demo_environment: dict[str, str], setting: str, value: str
) -> None:
    with pytest.raises(ConfigurationError) as raised:
        ApiConfiguration.from_environment(demo_environment | {f"NCI_API_{setting}": value})
    assert _SECRET not in str(raised.value) + repr(raised.value)
    assert raised.value.__context__ is None
    assert str(raised.value) in {
        "Invalid API configuration. Check the approved settings.",
        "Invalid API bind port.",
        "Invalid API bearer expiry timestamp.",
        "Loopback bearer expiry must be UTC and within eight hours.",
        "Unrecognised or invalid API environment setting.",
    }


@pytest.mark.parametrize(
    "required", ["BEARER_SECRET", "BEARER_EXPIRES_AT", "BUNDLE_ROOT", "RELEASE_SHA256"]
)
def test_demo_requires_pinned_evidence_and_valid_bearer(
    demo_environment: dict[str, str], required: str
) -> None:
    del demo_environment[f"NCI_API_{required}"]
    with pytest.raises(ConfigurationError):
        ApiConfiguration.from_environment(demo_environment)


def test_in_process_rejects_listener_and_unpaired_evidence() -> None:
    for env in (
        {"NCI_API_BIND_HOST": "127.0.0.1"},
        {"NCI_API_BIND_PORT": "8000"},
        {"NCI_API_BEARER_SECRET": _SECRET},
        {"NCI_API_BUNDLE_ROOT": "/fixtures/research"},
    ):
        with pytest.raises(ConfigurationError):
            ApiConfiguration.from_environment(env)


def test_in_process_accepts_pinned_bundle_settings() -> None:
    settings = ApiConfiguration(bundle_root=Path("/fixtures/research"), release_sha256="b" * 64)
    assert settings.mode == "in-process"
    assert settings.bundle_root == Path("/fixtures/research")


def test_startup_rechecks_expiry(
    demo_environment: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = ApiConfiguration.from_environment(demo_environment)

    class LaterDateTime:
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            return _NOW + timedelta(hours=1)

    monkeypatch.setattr(configuration, "datetime", LaterDateTime)
    with pytest.raises(ConfigurationError, match="expiry"):
        settings.check_startup()
