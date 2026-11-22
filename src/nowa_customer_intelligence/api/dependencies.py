"""Explicit dependencies for the application lifespan and future read routes."""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from starlette.requests import Request

from .configuration import ApiConfiguration
from .errors import ApiFailure, ErrorCode


class ResearchCatalogue(Protocol):
    """Identity exposed by a future verified catalogue or a test double."""

    @property
    def release_id(self) -> str: ...


type CatalogueLifespan = Callable[
    [ApiConfiguration], AbstractAsyncContextManager[ResearchCatalogue | None]
]


@dataclass(frozen=True, slots=True)
class ServiceIdentity:
    title: str
    contract_version: str
    service_version: str


@dataclass(frozen=True, slots=True)
class FoundationState:
    configuration: ApiConfiguration
    service: ServiceIdentity
    catalogue: ResearchCatalogue | None = None


def get_foundation_state(request: Request) -> FoundationState:
    state: FoundationState = request.app.state.foundation
    return state


def get_request_id(request: Request) -> UUID:
    request_id: UUID = request.state.request_id
    return request_id


def require_catalogue(request: Request) -> ResearchCatalogue:
    catalogue = get_foundation_state(request).catalogue
    if catalogue is None:
        raise ApiFailure(ErrorCode.EVIDENCE_UNAVAILABLE)
    return catalogue
