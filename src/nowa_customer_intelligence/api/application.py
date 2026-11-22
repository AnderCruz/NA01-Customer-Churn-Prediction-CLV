"""Application factory and ASGI lifecycle for the internal API."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, nullcontext
from dataclasses import replace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from .. import __version__
from .configuration import ApiConfiguration
from .dependencies import CatalogueLifespan, FoundationState, ServiceIdentity, get_request_id
from .errors import ApiFailure, ErrorCode, error_response, http_error_code


class LifecycleError(RuntimeError):
    """A sanitised failure while acquiring or releasing an application dependency."""


def create_app(
    configuration: ApiConfiguration | None = None,
    *,
    catalogue_lifespan: CatalogueLifespan | None = None,
) -> FastAPI:
    """Build a route-free application with no implicit I/O or network listener."""
    settings = (
        ApiConfiguration.model_validate(configuration)
        if configuration is not None
        else ApiConfiguration()
    )
    service = ServiceIdentity(
        title="Nowa Customer Intelligence — Internal Research & Analytics API",
        contract_version="1.0.0",
        service_version=__version__,
    )
    initial_state = FoundationState(settings, service)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings.check_startup()
        try:
            owner = (
                catalogue_lifespan(settings) if catalogue_lifespan is not None else nullcontext()
            )
            async with owner as catalogue:
                app.state.foundation = replace(initial_state, catalogue=catalogue)
                yield
        except Exception:
            pass
        else:
            return
        finally:
            app.state.foundation = initial_state
        raise LifecycleError("An API dependency failed during the application lifespan.")

    app = FastAPI(
        title=service.title,
        version=service.contract_version,
        lifespan=lifespan,
        debug=False,
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
        redirect_slashes=False,
    )
    app.state.foundation = initial_state

    @app.middleware("http")
    async def request_boundary(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = uuid4()
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            # Consume the exception before the ASGI server can log its contents.
            response = error_response(ErrorCode.INTERNAL_ERROR, request_id)
        response.headers["X-Request-ID"] = str(request_id)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ApiFailure)
    async def expected_failure(request: Request, exc: ApiFailure) -> Response:
        return error_response(exc.code, get_request_id(request))

    @app.exception_handler(HTTPException)
    async def http_failure(request: Request, exc: HTTPException) -> Response:
        return error_response(http_error_code(exc.status_code), get_request_id(request))

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> Response:
        return error_response(ErrorCode.VALIDATION_ERROR, get_request_id(request))

    return app
