"""Application factory and ASGI lifecycle for the internal API."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import replace
from time import perf_counter_ns
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import TypeAdapter, ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from .. import __version__
from .audit import record_request
from .configuration import ApiConfiguration
from .contracts import Slug
from .dependencies import CatalogueLifespan, FoundationState, ServiceIdentity, get_request_id
from .errors import ApiFailure, ErrorCode, error_response, http_error_code
from .research import verified_release
from .routes import approved_routes
from .security import PrincipalProvider, check_local_authority


class LifecycleError(RuntimeError):
    """A sanitised failure while acquiring or releasing an application dependency."""


def create_app(
    configuration: ApiConfiguration | None = None,
    *,
    catalogue_lifespan: CatalogueLifespan | None = None,
    principal_provider: PrincipalProvider | None = None,
) -> FastAPI:
    """Build the internal application without starting a network listener."""
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
            owner = (catalogue_lifespan or verified_release)(settings)
            async with owner as catalogue:
                if catalogue is not None:
                    try:
                        TypeAdapter(Slug).validate_python(catalogue.release_id, strict=True)
                    except ValidationError:
                        catalogue = None
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
        description=(
            "Read-only analytical research on authorised synthetic evidence. "
            "Model results do not establish commercial predictive validity or causality."
        ),
        lifespan=lifespan,
        debug=False,
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
        redirect_slashes=False,
    )
    app.state.foundation = initial_state

    def safe_error(request: Request, code: ErrorCode) -> Response:
        request.state.error_code = code
        return error_response(code, get_request_id(request))

    @app.middleware("http")
    async def request_boundary(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started_ns = perf_counter_ns()
        request_id = uuid4()
        request.state.request_id = request_id
        try:
            raw_path = request.scope.get("raw_path", request.url.path.encode())
            query = request.scope["query_string"]
            if len(raw_path) + len(query) + bool(query) > 2048:
                raise ApiFailure(ErrorCode.URI_TOO_LONG)
            if sum(len(key) + len(value) + 4 for key, value in request.scope["headers"]) > 8192:
                raise ApiFailure(ErrorCode.HEADERS_TOO_LARGE)
            check_local_authority(request, settings)
            size = 0
            if request.method == "GET":
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 1024:
                        raise ApiFailure(ErrorCode.PAYLOAD_TOO_LARGE)
                if size:
                    raise ApiFailure(ErrorCode.INVALID_REQUEST)
            response = await call_next(request)
        except ApiFailure as exc:
            response = safe_error(request, exc.code)
        except Exception:
            # Consume the exception before the ASGI server can log its contents.
            response = safe_error(request, ErrorCode.INTERNAL_ERROR)
        response.headers["X-Request-ID"] = str(request_id)
        response.headers["Cache-Control"] = "no-store"
        record_request(request, request_id, response.status_code, started_ns)
        return response

    @app.exception_handler(ApiFailure)
    async def expected_failure(request: Request, exc: ApiFailure) -> Response:
        return safe_error(request, exc.code)

    @app.exception_handler(HTTPException)
    async def http_failure(request: Request, exc: HTTPException) -> Response:
        return safe_error(request, http_error_code(exc.status_code))

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> Response:
        return safe_error(request, ErrorCode.VALIDATION_ERROR)

    app.include_router(approved_routes(principal_provider))
    return app
