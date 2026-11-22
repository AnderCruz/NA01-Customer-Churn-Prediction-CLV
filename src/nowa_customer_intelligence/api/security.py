"""Request access rules for in-process and authenticated loopback use."""

import hmac
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.requests import HTTPConnection, Request

from .configuration import ApiConfiguration
from .dependencies import get_foundation_state
from .errors import ApiFailure, ErrorCode

_TOKEN = re.compile(r"Bearer ([A-Za-z0-9_-]{32,128})", re.ASCII | re.IGNORECASE)
_FORWARDED = frozenset({"forwarded", "x-real-ip"})
RESEARCH_SCOPE = "research:read"
SYNTHETIC_AUDIENCE = "fieldwise-fictional"


@dataclass(frozen=True, slots=True)
class ResearchPrincipal:
    scope: str
    audience: str


type PrincipalProvider = Callable[[], ResearchPrincipal | None]


class ResearchBearer(HTTPBearer):
    """Describe HTTP bearer in OpenAPI and enforce the approved access policy."""

    def __init__(self, principal_provider: PrincipalProvider | None) -> None:
        super().__init__(scheme_name="ResearchBearer", auto_error=False)
        self._principal_provider = principal_provider

    async def __call__(self, request: HTTPConnection) -> HTTPAuthorizationCredentials | None:
        settings = get_foundation_state(request).configuration
        if settings.mode == "loopback":
            headers = request.headers.getlist("authorization")
            match = _TOKEN.fullmatch(headers[0]) if len(headers) == 1 else None
            expiry = settings.bearer_expires_at
            secret = settings.bearer_secret
            if (
                match is None
                or expiry is None
                or expiry <= datetime.now(UTC)
                or secret is None
                or not hmac.compare_digest(match[1], secret.get_secret_value())
            ):
                raise ApiFailure(ErrorCode.AUTH_REQUIRED)
            return None

        principal = self._principal_provider() if self._principal_provider is not None else None
        if principal is None:
            raise ApiFailure(ErrorCode.AUTH_REQUIRED)
        if (principal.scope, principal.audience) != (RESEARCH_SCOPE, SYNTHETIC_AUDIENCE):
            raise ApiFailure(ErrorCode.FORBIDDEN)
        return None


def check_local_authority(request: Request, settings: ApiConfiguration) -> None:
    """Enforce the HTTP authority independently of the future listener."""
    if any(name in _FORWARDED or name.startswith("x-forwarded-") for name in request.headers):
        raise ApiFailure(ErrorCode.INVALID_REQUEST)
    if settings.mode != "loopback":
        return
    host = settings.bind_host
    authority = f"[{host}]" if host == "::1" else host
    if (
        request.client is None
        or request.client.host not in {"127.0.0.1", "::1"}
        or request.headers.getlist("host") != [f"{authority}:{settings.bind_port}"]
    ):
        raise ApiFailure(ErrorCode.INVALID_REQUEST)
