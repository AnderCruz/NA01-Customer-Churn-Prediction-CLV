"""Load one independently pinned set of projected reports during startup."""

import json
import os
import stat
from collections import Counter
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import ValidationError
from starlette.requests import Request

from .. import __version__
from .audit import record_evidence
from .configuration import ApiConfiguration
from .contracts import (
    CHURN_FEATURES,
    CHURN_SHA,
    CLV_FEATURES,
    CLV_SHA,
    ChurnEvaluationData,
    ChurnEvaluationResponse,
    ChurnExplainabilityResponse,
    ChurnModelCard,
    ClvEvaluationData,
    ClvEvaluationResponse,
    ClvExplainabilityResponse,
    ClvModelCard,
    EvaluationResponse,
    ExplainabilityResponse,
    ExplanationData,
    LimitationsResponse,
    ModelCard,
    ModelListResponse,
    ModelResponse,
    Projection,
    Provenance,
    ReleaseManifestV1,
    ReleaseMember,
    ResponseContract,
    SegmentationData,
    SegmentationResponse,
)
from .dependencies import require_catalogue
from .errors import ApiFailure, ErrorCode

_RECORDS = {
    "churn-evaluation": ("nci-phase06-v1", "churn", CHURN_SHA, CHURN_FEATURES),
    "clv-evaluation": ("fieldwise-clv-v1", "clv", CLV_SHA, CLV_FEATURES),
    "churn-explainability": ("phase09-explainability-v1", "churn", CHURN_SHA, CHURN_FEATURES),
    "clv-explainability": ("phase09-explainability-v1", "clv", CLV_SHA, CLV_FEATURES),
    "segmentation-status": ("fieldwise-segmentation-v0", None, None, None),
}
_MANIFEST = "release.json"
_REPORT_LIMIT = 64 * 1024
_MANIFEST_LIMIT = 16 * 1024


class EvidenceDigestError(ValueError):
    """The pinned byte digest or length did not match."""


class EvidencePolicyError(ValueError):
    """The release contains an unapproved identity or file."""


class EvidenceVersionError(ValueError):
    """The release or experiment version is unsupported."""


@dataclass(frozen=True, slots=True)
class VerifiedCatalogue:
    release_id: str
    cards: ModelListResponse
    churn_evaluation: ChurnEvaluationResponse
    clv_evaluation: ClvEvaluationResponse
    churn_explanations: ChurnExplainabilityResponse
    clv_explanations: ClvExplainabilityResponse
    churn_limitations: LimitationsResponse
    clv_limitations: LimitationsResponse
    segmentation: SegmentationResponse

    def model(self, model_id: str) -> ModelCard:
        for card in self.cards.models:
            if card.model_id == model_id:
                return card
        raise ApiFailure(ErrorCode.NOT_FOUND)

    def evaluation(self, model_id: str) -> EvaluationResponse:
        card = self.model(model_id)
        return self.churn_evaluation if card.model_id == "churn" else self.clv_evaluation

    def explanation(self, model_id: str) -> ExplainabilityResponse:
        card = self.model(model_id)
        return self.churn_explanations if card.model_id == "churn" else self.clv_explanations

    def limitations(self, model_id: str) -> LimitationsResponse:
        card = self.model(model_id)
        return self.churn_limitations if card.model_id == "churn" else self.clv_limitations


def require_verified_catalogue(request: Request) -> VerifiedCatalogue:
    catalogue = require_catalogue(request)
    if not isinstance(catalogue, VerifiedCatalogue):
        raise ApiFailure(ErrorCode.EVIDENCE_UNAVAILABLE)
    return catalogue


@contextmanager
def _open_root(path: Path) -> Iterator[int]:
    if os.open not in os.supports_dir_fd or os.listdir not in os.supports_fd:
        raise ValueError("Secure directory-relative reads are unavailable.")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = os.open("/", flags)
    try:
        for component in path.parts[1:]:
            child = os.open(component, flags, dir_fd=directory)
            os.close(directory)
            directory = child
        yield directory
    finally:
        os.close(directory)


def _checked_read(directory: int, basename: str, limit: int, pin: str) -> bytes:
    fd = os.open(basename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or not 1 <= info.st_size <= limit:
            raise ValueError("Invalid release file type or size.")
        with os.fdopen(fd, "rb", closefd=False) as source:
            data = source.read(limit + 1)
    finally:
        os.close(fd)
    if len(data) != info.st_size or sha256(data).hexdigest() != pin:
        raise EvidenceDigestError
    return data


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate evidence JSON member.")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError("Non-finite JSON value.")


def _parse[T: ResponseContract](schema: type[T], data: bytes) -> T:
    raw = json.loads(
        data.decode("utf-8"), object_pairs_hook=_strict_object, parse_constant=_reject_nonfinite
    )
    if isinstance(raw, dict):
        if schema is ReleaseManifestV1 and type(raw.get("schema_version")) is int:
            if raw["schema_version"] != 1:
                raise EvidenceVersionError
        elif schema is ReleaseManifestV1:
            raise ValueError("Invalid release schema version type.")
        elif "schema_id" in raw and raw["schema_id"] != "research-projection-v1":
            raise EvidenceVersionError
    return schema.model_validate_json(data)


def _projection[T: ResponseContract](
    schema: type[Projection[T]],
    directory: int,
    member: ReleaseMember,
) -> T:
    data = _checked_read(directory, member.basename, _REPORT_LIMIT, member.sha256)
    if len(data) != member.size_bytes:
        raise ValueError("Manifest size disagrees with the verified file.")
    projected = _parse(schema, data)
    if projected.report_id != member.report_id:
        raise ValueError("Unexpected research report identity.")
    return projected.data


def _validate_member(member: ReleaseMember) -> None:
    experiment, model_id, fingerprint, feature_version = _RECORDS[member.report_id]
    if member.experiment_id != experiment:
        raise EvidenceVersionError
    if member.basename != f"{member.report_id}.json" or (
        member.experiment_id,
        member.model_id,
        member.model_version,
        member.feature_contract_version,
    ) != (experiment, model_id, fingerprint, feature_version):
        raise EvidencePolicyError
    if (
        model_id is None
        and {"model_id", "model_version", "feature_contract_version"} & member.model_fields_set
    ):
        raise ValueError("Segmentation must omit model provenance.")


def _provenance(manifest: ReleaseManifestV1, member: ReleaseMember) -> Provenance:
    optional: dict[str, object] = {}
    if member.feature_contract_version is not None:
        optional["feature_contract_version"] = member.feature_contract_version
    if manifest.published_at is not None:
        optional["published_at"] = manifest.published_at
    return Provenance.model_validate(
        {
            "report_id": member.report_id,
            "experiment_id": member.experiment_id,
            "report_schema_version": member.schema_id,
            "report_sha256": member.sha256,
            "source_report_sha256": member.source_report_sha256,
            "audited_commit": manifest.audited_commit,
            **optional,
        }
    )


def _validate_explanations(
    evidence: ExplanationData,
    model_id: Literal["churn", "clv"],
) -> None:
    expected = {
        "churn": ("class-1-probability", "class-1-log-odds"),
        "clv": ("clipped-gross-issued-gbp",),
    }
    extra = "weak-churn-validation" if model_id == "churn" else "correlated-billing-fields"
    required = {"model-behaviour-only", "background-dependent", "no-causal-effects", extra}
    if tuple(method.output_scale for method in evidence.methods) != expected[model_id]:
        raise ValueError("Unsupported explanation scale or order.")
    if len(evidence.limitation_ids) != len(required) or set(evidence.limitation_ids) != required:
        raise ValueError("Unexpected explanation limitation IDs.")


def _read_catalogue(root: Path, digest: str) -> VerifiedCatalogue:
    with _open_root(root) as directory:
        names = {_MANIFEST, *(f"{report}.json" for report in _RECORDS)}
        actual = set(os.listdir(directory))
        if names - actual:
            raise FileNotFoundError
        if actual - names:
            raise EvidencePolicyError
        manifest = _parse(
            ReleaseManifestV1, _checked_read(directory, _MANIFEST, _MANIFEST_LIMIT, digest)
        )
        members = {item.report_id: item for item in manifest.members}
        if len(members) != len(manifest.members) or set(members) != set(_RECORDS):
            raise ValueError("Incomplete or duplicate manifest entries.")
        for member in members.values():
            _validate_member(member)
        churn = _projection(Projection[ChurnEvaluationData], directory, members["churn-evaluation"])
        clv = _projection(Projection[ClvEvaluationData], directory, members["clv-evaluation"])
        churn_xai = _projection(
            Projection[ExplanationData], directory, members["churn-explainability"]
        )
        clv_xai = _projection(Projection[ExplanationData], directory, members["clv-explainability"])
        segmentation = _projection(
            Projection[SegmentationData], directory, members["segmentation-status"]
        )

    _validate_explanations(churn_xai, "churn")
    _validate_explanations(clv_xai, "clv")
    for record in (churn, clv):
        if Counter(item.id for item in record.limitations) != Counter(record.model.limitation_ids):
            raise ValueError("Inconsistent evaluation limitations.")

    provenance: dict[str, Provenance] = {
        key: _provenance(manifest, value) for key, value in members.items()
    }
    return _assemble(manifest, provenance, churn, clv, churn_xai, clv_xai, segmentation)


def _assemble(
    manifest: ReleaseManifestV1,
    provenance: dict[str, Provenance],
    churn: ChurnEvaluationData,
    clv: ClvEvaluationData,
    churn_xai: ExplanationData,
    clv_xai: ExplanationData,
    segmentation: SegmentationData,
) -> VerifiedCatalogue:
    header = {
        "api_version": "v1",
        "service_version": __version__,
        "schema_version": 1,
        "evidence_version": manifest.release_id,
    }
    churn_card = ChurnModelCard(
        **churn.model.model_dump(), provenance=provenance["churn-evaluation"]
    )
    clv_card = ClvModelCard(**clv.model.model_dump(), provenance=provenance["clv-evaluation"])
    cards = ModelListResponse.model_validate(header | {"models": (churn_card, clv_card)})
    churn_eval = ChurnEvaluationResponse.model_validate(
        header
        | {
            "model": churn_card,
            "metrics": churn.metrics,
            "provenance": churn_card.provenance,
            "partition": churn.partition,
            "observations": churn.observations,
            "accounts": churn.accounts,
        }
    )
    clv_eval = ClvEvaluationResponse.model_validate(
        header
        | {
            "model": clv_card,
            "metrics": clv.metrics,
            "provenance": clv_card.provenance,
            "partition": clv.partition,
            "observations": clv.observations,
            "accounts": clv.accounts,
        }
    )
    interpretation = {"interpretation": "model-association", "causal": False}
    churn_explain = ChurnExplainabilityResponse.model_validate(
        header
        | interpretation
        | {
            "model": churn_card,
            "provenance": provenance["churn-explainability"],
            "methods": churn_xai.methods,
            "limitation_ids": churn_xai.limitation_ids,
        }
    )
    clv_explain = ClvExplainabilityResponse.model_validate(
        header
        | interpretation
        | {
            "model": clv_card,
            "provenance": provenance["clv-explainability"],
            "methods": clv_xai.methods,
            "limitation_ids": clv_xai.limitation_ids,
        }
    )
    churn_limits = LimitationsResponse.model_validate(
        header | {"model": churn_card, "limitations": churn.limitations}
    )
    clv_limits = LimitationsResponse.model_validate(
        header | {"model": clv_card, "limitations": clv.limitations}
    )
    segmentation_response = SegmentationResponse.model_validate(
        header | segmentation.model_dump() | {"provenance": provenance["segmentation-status"]}
    )
    for response, ceiling in (
        (cards, 16),
        (churn_eval, 16),
        (clv_eval, 16),
        (churn_explain, 16),
        (clv_explain, 16),
        (churn_limits, 8),
        (clv_limits, 8),
        (segmentation_response, 8),
        (ModelResponse.model_validate(header | {"model": churn_card}), 8),
        (ModelResponse.model_validate(header | {"model": clv_card}), 8),
    ):
        if len(response.model_dump_json(exclude_unset=True).encode()) > ceiling * 1024:
            raise ValueError("Research response exceeds its approved payload ceiling.")
    return VerifiedCatalogue(
        manifest.release_id,
        cards,
        churn_eval,
        clv_eval,
        churn_explain,
        clv_explain,
        churn_limits,
        clv_limits,
        segmentation_response,
    )


@asynccontextmanager
async def verified_release(settings: ApiConfiguration) -> AsyncIterator[VerifiedCatalogue | None]:
    if settings.bundle_root is None or settings.release_sha256 is None:
        record_evidence("MISSING_EVIDENCE")
        yield None
        return
    catalogue = None
    try:
        catalogue = _read_catalogue(settings.bundle_root, settings.release_sha256)
    except FileNotFoundError:
        record_evidence("MISSING_EVIDENCE")
    except EvidenceDigestError:
        record_evidence("DIGEST_MISMATCH")
    except EvidenceVersionError:
        record_evidence("UNSUPPORTED_VERSION")
    except EvidencePolicyError:
        record_evidence("POLICY_DENIED")
    except (OSError, ValueError, ValidationError, RecursionError):
        record_evidence("SCHEMA_INVALID")
    else:
        record_evidence("VERIFIED", catalogue.release_id)
    yield catalogue
