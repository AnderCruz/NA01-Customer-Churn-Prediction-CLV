"""The nine approved internal research API routes."""

from json import loads
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request, Security

from .contracts import (
    CapabilitiesResponse,
    EvaluationResponse,
    ExplainabilityResponse,
    LimitationsResponse,
    LivenessResponse,
    ModelListResponse,
    ModelResponse,
    ReadinessResponse,
    ResearchCapability,
    SegmentationResponse,
)
from .dependencies import ResearchCatalogue, get_foundation_state, require_catalogue
from .errors import ApiError, ApiFailure, ErrorCode, error_response, http_error_code
from .research import require_verified_catalogue
from .security import PrincipalProvider, ResearchBearer


def _response_docs(
    *statuses: int,
    evidence_unavailable: bool = False,
) -> dict[int | str, dict[str, object]]:
    documented: dict[int | str, dict[str, object]] = {}
    for status in statuses:
        headers = {
            "X-Request-ID": {"schema": {"type": "string", "format": "uuid"}},
            "Cache-Control": {"schema": {"type": "string", "const": "no-store"}},
        }
        if status == 401:
            headers["WWW-Authenticate"] = {"schema": {"type": "string", "const": "Bearer"}}
        if status == 405:
            headers["Allow"] = {"schema": {"type": "string", "const": "GET"}}
        response: dict[str, object] = {"headers": headers}
        if status != 200:
            response["model"] = ApiError
            code = (
                ErrorCode.EVIDENCE_UNAVAILABLE
                if status == 503 and evidence_unavailable
                else http_error_code(status)
            )
            example = error_response(code, UUID("2596c735-5cec-4bde-a4f3-c6fcdef9ac66"))
            assert isinstance(example.body, bytes)
            response["content"] = {"application/json": {"example": loads(example.body)}}
        documented[status] = response
    return documented


TRANSPORT_ERRORS = _response_docs(200, 400, 405, 413, 414, 422, 431, 500)
RESEARCH_ERRORS = TRANSPORT_ERRORS | _response_docs(401, 403, 503, evidence_unavailable=True)
MODEL_ERRORS = RESEARCH_ERRORS | _response_docs(404)
RESEARCH_DESCRIPTION = "Requires research:read for fieldwise-fictional. Synthetic research only."
ModelParameter = Annotated[
    str,
    Path(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", max_length=48),
]


def empty_query(request: Request) -> None:
    if request.url.query:
        raise ApiFailure(ErrorCode.VALIDATION_ERROR)


def research_router(principal_provider: PrincipalProvider | None) -> APIRouter:
    return APIRouter(
        dependencies=[Security(ResearchBearer(principal_provider)), Depends(empty_query)]
    )


def approved_routes(principal_provider: PrincipalProvider | None) -> APIRouter:
    router = APIRouter()
    research = research_router(principal_provider)

    @router.get(
        "/health/live",
        operation_id="getLiveness",
        tags=["Health"],
        responses=TRANSPORT_ERRORS,
        dependencies=[Depends(empty_query)],
    )
    async def live() -> LivenessResponse:
        return LivenessResponse(status="live")

    @router.get(
        "/health/ready",
        operation_id="getReadiness",
        tags=["Health"],
        responses=TRANSPORT_ERRORS | _response_docs(503),
        dependencies=[Depends(empty_query)],
    )
    async def ready(request: Request) -> ReadinessResponse:
        if get_foundation_state(request).catalogue is None:
            raise ApiFailure(ErrorCode.SERVICE_UNAVAILABLE)
        return ReadinessResponse(status="ready")

    @research.get(
        "/v1/research/capabilities",
        operation_id="listResearchCapabilities",
        description=RESEARCH_DESCRIPTION,
        tags=["Research capabilities"],
        responses=RESEARCH_ERRORS,
    )
    async def capabilities(
        request: Request,
        catalogue: Annotated[ResearchCatalogue, Depends(require_catalogue)],
    ) -> CapabilitiesResponse:
        return CapabilitiesResponse(
            api_version="v1",
            service_version=get_foundation_state(request).service.service_version,
            schema_version=1,
            evidence_version=catalogue.release_id,
            capabilities=(
                ResearchCapability(capability_id="models", status="available"),
                ResearchCapability(capability_id="evaluation", status="available"),
                ResearchCapability(capability_id="limitations", status="available"),
                ResearchCapability(capability_id="explainability", status="available"),
                ResearchCapability(capability_id="segmentation-status", status="available"),
            ),
        )

    @research.get(
        "/v1/research/models",
        operation_id="listResearchModels",
        description=RESEARCH_DESCRIPTION,
        tags=["Research models"],
        responses=RESEARCH_ERRORS,
        response_model_exclude_none=True,
    )
    async def models(request: Request) -> ModelListResponse:
        return require_verified_catalogue(request).cards

    @research.get(
        "/v1/research/models/{model_id}",
        operation_id="getResearchModel",
        description=RESEARCH_DESCRIPTION,
        tags=["Research models"],
        responses=MODEL_ERRORS,
        response_model_exclude_none=True,
    )
    async def model(
        request: Request,
        model_id: ModelParameter,
    ) -> ModelResponse:
        catalogue = require_verified_catalogue(request)
        return ModelResponse(
            api_version=catalogue.cards.api_version,
            service_version=catalogue.cards.service_version,
            schema_version=catalogue.cards.schema_version,
            evidence_version=catalogue.release_id,
            model=catalogue.model(model_id),
        )

    @research.get(
        "/v1/research/models/{model_id}/evaluation",
        operation_id="getResearchEvaluation",
        description=RESEARCH_DESCRIPTION,
        tags=["Research models"],
        responses=MODEL_ERRORS,
        response_model_exclude_unset=True,
    )
    async def evaluation(request: Request, model_id: ModelParameter) -> EvaluationResponse:
        return require_verified_catalogue(request).evaluation(model_id)

    @research.get(
        "/v1/research/models/{model_id}/limitations",
        operation_id="getResearchLimitations",
        description=RESEARCH_DESCRIPTION,
        tags=["Research models"],
        responses=MODEL_ERRORS,
        response_model_exclude_unset=True,
    )
    async def limitations(request: Request, model_id: ModelParameter) -> LimitationsResponse:
        return require_verified_catalogue(request).limitations(model_id)

    @research.get(
        "/v1/research/models/{model_id}/explainability",
        operation_id="getResearchExplainability",
        description=RESEARCH_DESCRIPTION,
        tags=["Research models"],
        responses=MODEL_ERRORS,
        response_model_exclude_unset=True,
    )
    async def explanation(request: Request, model_id: ModelParameter) -> ExplainabilityResponse:
        return require_verified_catalogue(request).explanation(model_id)

    @research.get(
        "/v1/research/segmentation/status",
        operation_id="getResearchSegmentationStatus",
        description=RESEARCH_DESCRIPTION,
        tags=["Segmentation research"],
        responses=RESEARCH_ERRORS,
        response_model_exclude_unset=True,
    )
    async def segmentation(request: Request) -> SegmentationResponse:
        return require_verified_catalogue(request).segmentation

    router.include_router(research)
    return router
