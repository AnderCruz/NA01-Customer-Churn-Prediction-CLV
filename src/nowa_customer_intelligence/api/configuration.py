"""Strict, local-only configuration for the API foundation."""

import re
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ModelWrapValidatorHandler,
    SecretStr,
    ValidationError,
    model_validator,
)

_ENV_PREFIX = "NCI_API_"
_BEARER = re.compile(r"[A-Za-z0-9_-]{32,128}")
_UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", re.ASCII)
_FIELDS = {
    "MODE": "mode",
    "BUNDLE_ROOT": "bundle_root",
    "RELEASE_SHA256": "release_sha256",
    "BIND_HOST": "bind_host",
    "BIND_PORT": "bind_port",
    "BEARER_SECRET": "bearer_secret",
    "BEARER_EXPIRES_AT": "bearer_expires_at",
    "LOG_LEVEL": "log_level",
}


class ConfigurationError(RuntimeError):
    """A configuration failure safe to display to the operator."""


class ApiConfiguration(BaseModel):
    """Validated settings. Loading from the process environment is explicit."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        revalidate_instances="always",
    )

    mode: Literal["in-process", "loopback"] = "in-process"
    bundle_root: Path | None = Field(default=None, repr=False)
    release_sha256: (
        Annotated[str, Field(pattern=r"^[a-f0-9]{64}$", min_length=64, max_length=64)] | None
    ) = None
    bind_host: Literal["127.0.0.1", "::1"] | None = None
    bind_port: Annotated[int, Field(ge=1024, le=65535)] | None = None
    bearer_secret: SecretStr | None = Field(default=None, repr=False, exclude=True)
    bearer_expires_at: datetime | None = None
    log_level: Literal["INFO", "WARNING"] = "INFO"

    @model_validator(mode="before")
    @classmethod
    def _loopback_defaults(cls, value: object) -> object:
        if isinstance(value, dict) and value.get("mode") == "loopback":
            return {"bind_host": "127.0.0.1", "bind_port": 8000, **value}
        return value

    @model_validator(mode="after")
    def _check_mode(self) -> Self:
        if (self.bundle_root is None) != (self.release_sha256 is None):
            raise ValueError("The bundle root and release digest must be supplied together.")
        if self.bundle_root is not None and (
            not self.bundle_root.is_absolute()
            or ".." in self.bundle_root.parts
            or "\0" in str(self.bundle_root)
        ):
            raise ValueError("The bundle root must be absolute and free of parent traversal.")

        local_settings = (
            self.bind_host,
            self.bind_port,
            self.bearer_secret,
            self.bearer_expires_at,
        )
        if self.mode == "in-process":
            if any(value is not None for value in local_settings):
                raise ValueError("Listener and bearer settings require loopback mode.")
            return self

        if self.bundle_root is None or any(value is None for value in local_settings):
            raise ValueError("Loopback requires a pinned bundle, local bind and bearer settings.")
        if self.bearer_secret is None or not _BEARER.fullmatch(
            self.bearer_secret.get_secret_value()
        ):
            raise ValueError("The bearer secret has an invalid format.")
        self.check_startup()
        return self

    @model_validator(mode="wrap")
    @classmethod
    def _hide_validation_details(
        cls, value: object, handler: ModelWrapValidatorHandler[Self]
    ) -> Self:
        try:
            return handler(value)
        except ValidationError:
            pass
        raise ConfigurationError("Invalid API configuration. Check the approved settings.")

    def check_startup(self) -> None:
        """Recheck the credential lifetime immediately before starting the lifespan."""
        if self.mode == "loopback":
            now = datetime.now(UTC)
            expiry = self.bearer_expires_at
            if (
                expiry is None
                or expiry.utcoffset() != timedelta(0)
                or not (now < expiry <= now + timedelta(hours=8))
            ):
                raise ConfigurationError(
                    "Loopback bearer expiry must be UTC and within eight hours."
                )

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> Self:
        """Parse the approved environment namespace without echoing input values."""
        settings: dict[str, object] = {}
        for name, value in environment.items():
            if not name.startswith(_ENV_PREFIX):
                continue
            key = _FIELDS.get(name.removeprefix(_ENV_PREFIX))
            if key is None or not isinstance(value, str):
                raise ConfigurationError("Unrecognised or invalid API environment setting.")
            if key == "bundle_root":
                if "\0" in value:
                    raise ConfigurationError("Invalid API bundle root.")
                settings[key] = Path(value)
            elif key == "bind_port":
                if not re.fullmatch(r"[0-9]{4,5}", value):
                    raise ConfigurationError("Invalid API bind port.")
                settings[key] = int(value)
            elif key == "bearer_expires_at":
                if not _UTC_TIMESTAMP.fullmatch(value):
                    raise ConfigurationError("Invalid API bearer expiry timestamp.")
                try:
                    settings[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
                if key not in settings:
                    raise ConfigurationError("Invalid API bearer expiry timestamp.")
            else:
                settings[key] = value
        return cls.model_validate(settings)
