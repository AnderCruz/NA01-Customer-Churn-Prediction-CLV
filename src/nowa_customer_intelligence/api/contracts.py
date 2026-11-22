"""Public response models for the internal Research & Analytics API."""

import re
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Annotated, ClassVar, Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Discriminator,
    Field,
    PlainSerializer,
    StringConstraints,
    Tag,
    WithJsonSchema,
    field_validator,
    model_validator,
)

Slug = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", max_length=48),
]


class ResponseContract(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, allow_inf_nan=False)


class LivenessResponse(ResponseContract):
    status: Literal["live"]


class ReadinessResponse(ResponseContract):
    status: Literal["ready"]


class ServiceMetadata(ResponseContract):
    api_version: Literal["v1"]
    service_version: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    schema_version: Literal[1]
    evidence_version: Slug


type CapabilityId = Literal[
    "models", "evaluation", "limitations", "explainability", "segmentation-status"
]


class ResearchCapability(ResponseContract):
    capability_id: CapabilityId
    status: Literal["available"]


class CapabilitiesResponse(ServiceMetadata):
    capabilities: tuple[
        ResearchCapability,
        ResearchCapability,
        ResearchCapability,
        ResearchCapability,
        ResearchCapability,
    ]


# Runtime releases contain only these projected records and approved wire types.
Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
CommitId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
SafeText = Annotated[str, StringConstraints(min_length=1, max_length=240)]
Count = Annotated[int, Field(ge=0, le=2147483647)]
Fraction = Annotated[float, Field(ge=0, le=1)]
NonNegative = Annotated[float, Field(ge=0)]
Correlation = Annotated[float, Field(ge=-1, le=1)]


def _penny_decimal(value: object) -> Decimal:
    if isinstance(value, str) and re.fullmatch(r"-?[0-9]{1,12}(?:[.][0-9]{1,16})?", value):
        value = Decimal(value)
    if not isinstance(value, Decimal) or not value.is_finite() or abs(value) >= 10**12:
        raise ValueError("A bounded precise GBP decimal is required.")
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return abs(rounded) if rounded == 0 else rounded


Gbp = Annotated[
    Decimal,
    Field(max_digits=14, decimal_places=2),
    BeforeValidator(_penny_decimal),
    PlainSerializer(
        lambda amount: format(amount, ".2f"),
        return_type=str,
        when_used="json",
    ),
    WithJsonSchema(
        {"type": "string", "pattern": r"^-?[0-9]{1,12}[.][0-9]{2}$"}, mode="serialization"
    ),
]


def _unsigned_money(value: object) -> object:
    if (isinstance(value, str) and value.startswith("-")) or (
        isinstance(value, Decimal) and value.is_signed()
    ):
        raise ValueError("This GBP metric does not permit a sign.")
    return value


NonNegativeGbp = Annotated[
    Gbp,
    Field(ge=0),
    BeforeValidator(_unsigned_money),
    WithJsonSchema(
        {"type": "string", "pattern": r"^[0-9]{1,12}[.][0-9]{2}$"}, mode="serialization"
    ),
]
CHURN_SHA = "16d7a588ec36dc4b22beb20b56f98903af68d4453563921985ba063a024a8cd1"
CLV_SHA = "250f4d860a662f69f95e2577cd890dc4f86d75c33771bc8dc0ed04aa4398afc7"
CHURN_FEATURES = "fieldwise-episode-features-v1"
CLV_FEATURES = "fieldwise-clv-v1"
type ModelId = Literal["churn", "clv"]
type ReportId = Literal[
    "churn-evaluation",
    "clv-evaluation",
    "churn-explainability",
    "clv-explainability",
    "segmentation-status",
]
type LimitationId = Literal[
    "synthetic-only",
    "weak-churn-validation",
    "uncalibrated-for-operational-use",
    "no-operational-risk-bands",
    "billed-value-proxy",
    "no-operational-use",
    "model-behaviour-only",
    "background-dependent",
    "no-causal-effects",
    "correlated-billing-fields",
    "no-nominated-clustering-model",
]


class Provenance(ResponseContract):
    report_id: ReportId
    experiment_id: Slug
    report_schema_version: Literal["research-projection-v1"]
    report_sha256: Digest
    audited_commit: CommitId
    source_report_sha256: Digest
    feature_contract_version: Slug | None = None
    published_at: AwareDatetime | None = None


class ModelIdentity(ResponseContract):
    data_origin: Literal["fieldwise-fictional"]
    evaluation_status: Literal["experimental-development-validation"]
    production_approved: Literal[False]
    limitation_ids: Annotated[tuple[LimitationId, ...], Field(min_length=1, max_length=12)]
    required_limitations: ClassVar[frozenset[str]]

    @field_validator("production_approved", mode="before")
    @classmethod
    def explicit_boolean(cls, value: object) -> object:
        if type(value) is not bool:
            raise ValueError("Production approval must be a boolean.")
        return value

    @field_validator("horizon_value", mode="before", check_fields=False)
    @classmethod
    def explicit_horizon(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("Forecast horizon must be an integer.")
        return value

    @model_validator(mode="after")
    def check_limitations(self) -> Self:
        if set(self.limitation_ids) != self.required_limitations or len(self.limitation_ids) != len(
            self.required_limitations
        ):
            raise ValueError("Unexpected model limitation IDs.")
        return self


class ChurnIdentity(ModelIdentity):
    model_id: Literal["churn"]
    display_name: Literal["Contractual subscription churn"]
    model_family: Literal["HistGradientBoostingClassifier"]
    model_version: Literal["16d7a588ec36dc4b22beb20b56f98903af68d4453563921985ba063a024a8cd1"]
    entity: Literal["subscription-episode"]
    target: Literal["contractual-churn"]
    horizon_value: Literal[30]
    horizon_unit: Literal["day"]
    prediction_unit: Literal["class-1-probability"]
    required_limitations = frozenset(
        {
            "synthetic-only",
            "weak-churn-validation",
            "uncalibrated-for-operational-use",
            "no-operational-risk-bands",
        }
    )


class ClvIdentity(ModelIdentity):
    model_id: Literal["clv"]
    display_name: Literal["Six-month billed value"]
    model_family: Literal["HistGradientBoostingRegressor"]
    model_version: Literal["250f4d860a662f69f95e2577cd890dc4f86d75c33771bc8dc0ed04aa4398afc7"]
    entity: Literal["customer-account"]
    target: Literal["future_6m_issued_gbp"]
    horizon_value: Literal[6]
    horizon_unit: Literal["calendar-month"]
    prediction_unit: Literal["gross-issued-gbp"]
    required_limitations = frozenset({"synthetic-only", "billed-value-proxy", "no-operational-use"})


class ChurnModelCard(ChurnIdentity):
    provenance: Provenance


class ClvModelCard(ClvIdentity):
    provenance: Provenance


type ModelCard = Annotated[ChurnModelCard | ClvModelCard, Field(discriminator="model_id")]


class ModelResponse(ServiceMetadata):
    model: ModelCard


class ModelListResponse(ServiceMetadata):
    models: tuple[ChurnModelCard, ClvModelCard]


class Limitation(ResponseContract):
    id: LimitationId
    severity: Literal["restriction", "caution"]
    description: SafeText

    @field_validator("description")
    @classmethod
    def plain_text(cls, value: str) -> str:
        if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value):
            raise ValueError("Unexpected control character.")
        return value


class ChurnMetrics(ResponseContract):
    average_precision: Fraction
    roc_auc: Fraction
    precision: Fraction
    recall: Fraction
    brier: Fraction
    research_threshold: Fraction
    positive_accounts: Count
    false_positives: Count


class ClvMetrics(ResponseContract):
    mae_gbp: NonNegativeGbp
    rmse_gbp: NonNegativeGbp
    median_ae_gbp: NonNegativeGbp
    signed_bias_gbp: Gbp
    r2: Annotated[float, Field(le=1)] | None
    r2_unavailable_reason: Literal["undefined", "not-released"] | None = None

    @model_validator(mode="after")
    def check_reason(self) -> Self:
        if (self.r2 is None) != (self.r2_unavailable_reason is not None):
            raise ValueError("Missing or unexpected R² reason.")
        if self.r2 is not None and "r2_unavailable_reason" in self.model_fields_set:
            raise ValueError("The R² reason must be omitted for available values.")
        return self


class EvaluationScope(ResponseContract):
    partition: Literal["development-validation"]
    observations: Count
    accounts: Count

    @model_validator(mode="after")
    def check_support(self) -> Self:
        if not 1 <= self.accounts <= self.observations:
            raise ValueError("Invalid evaluation support.")
        return self


class ChurnEvaluationData(EvaluationScope):
    model: ChurnIdentity
    metrics: ChurnMetrics
    limitations: Annotated[tuple[Limitation, ...], Field(min_length=1, max_length=12)]


class ClvEvaluationData(EvaluationScope):
    model: ClvIdentity
    metrics: ClvMetrics
    limitations: Annotated[tuple[Limitation, ...], Field(min_length=1, max_length=12)]


type TermId = Literal[
    "episode_age_days",
    "latest_sessions",
    "expected_usage_months",
    "account-lifecycle",
    "invoice-history-and-cadence",
    "contract-snapshots",
    "calendar",
]


class AttributionTerm(ResponseContract):
    term_id: TermId
    mean_absolute: NonNegative


class ExplanationMethod(ResponseContract):
    method: Literal["tree-shap-interventional", "finite-background-block-shapley"]
    output_scale: Literal["class-1-probability", "class-1-log-odds", "clipped-gross-issued-gbp"]
    unit: Literal["probability", "log-odds", "GBP"]
    training_background_accounts: Count
    global_validation_accounts: Count
    reconciled_rows: Count
    failures: Literal[0]
    tolerance: Annotated[float, Field(gt=0)]
    max_error: NonNegative
    terms: Annotated[tuple[AttributionTerm, ...], Field(max_length=8)]
    background_rank_median: Correlation | None = None
    bootstrap_rank_median: Correlation | None = None

    @field_validator("failures", mode="before")
    @classmethod
    def explicit_failure_count(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("The failure count must be an integer.")
        return value

    @model_validator(mode="after")
    def check_method(self) -> Self:
        expected = {
            "class-1-probability": (
                "tree-shap-interventional",
                "probability",
                {"episode_age_days", "latest_sessions", "expected_usage_months"},
            ),
            "class-1-log-odds": ("tree-shap-interventional", "log-odds", set()),
            "clipped-gross-issued-gbp": (
                "finite-background-block-shapley",
                "GBP",
                {
                    "account-lifecycle",
                    "invoice-history-and-cadence",
                    "contract-snapshots",
                    "calendar",
                },
            ),
        }
        method, unit, terms = expected[self.output_scale]
        if (self.method, self.unit) != (method, unit) or (
            {term.term_id for term in self.terms} != terms or len(self.terms) != len(terms)
        ):
            raise ValueError("Unexpected attribution method or terms.")
        if self.max_error > self.tolerance or not (
            self.training_background_accounts > 0
            and 0 < self.global_validation_accounts <= self.reconciled_rows
        ):
            raise ValueError("Incompatible attribution reconciliation or support.")
        for key in ("background_rank_median", "bootstrap_rank_median"):
            if key in self.model_fields_set and (
                self.output_scale == "class-1-log-odds" or getattr(self, key) is None
            ):
                raise ValueError("Unavailable stability metrics must be omitted.")
        return self


class ExplanationData(ResponseContract):
    methods: Annotated[tuple[ExplanationMethod, ...], Field(min_length=1, max_length=2)]
    limitation_ids: Annotated[tuple[LimitationId, ...], Field(min_length=2, max_length=8)]


class SegmentationData(ResponseContract):
    method: Literal["rfm"]
    method_version: Literal["fieldwise-segmentation-v0"]
    data_origin: Literal["fieldwise-fictional"]
    evaluation_scope: Literal["synthetic-development-research"]
    nomination: Literal["none"]
    operational_assignment_available: Literal[False]
    dimensions: tuple[Literal["recency"], Literal["frequency"], Literal["monetary"]]
    limitation_ids: tuple[Literal["no-nominated-clustering-model"]]

    @field_validator("operational_assignment_available", mode="before")
    @classmethod
    def explicit_assignment_status(cls, value: object) -> object:
        if type(value) is not bool:
            raise ValueError("Operational assignment status must be a boolean.")
        return value


class ReleaseMember(ResponseContract):
    report_id: ReportId
    basename: SafeText
    experiment_id: Slug
    schema_id: Literal["research-projection-v1"]
    sha256: Digest
    source_report_sha256: Digest
    size_bytes: Annotated[int, Field(ge=1, le=65536)]
    model_id: ModelId | None = None
    model_version: Digest | None = None
    feature_contract_version: Slug | None = None


class ReleaseManifestV1(ResponseContract):
    schema_version: Literal[1]
    release_id: Slug
    audience: Literal["fieldwise-fictional"]
    audited_commit: CommitId
    published_at: AwareDatetime | None = None
    members: Annotated[tuple[ReleaseMember, ...], Field(min_length=5, max_length=5)]

    @field_validator("published_at", mode="before")
    @classmethod
    def wire_utc(cls, value: object) -> object:
        if not isinstance(value, str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:[.][0-9]{1,6})?Z",
            value,
        ):
            raise ValueError("The release timestamp must be an explicit UTC string.")
        return datetime.fromisoformat(value)

    @field_validator("published_at")
    @classmethod
    def canonical_utc(cls, value: datetime | None) -> datetime:
        if value is None or value.utcoffset() != timedelta(0):
            raise ValueError("Invalid published timestamp.")
        return value


class Projection[T](ResponseContract):
    schema_id: Literal["research-projection-v1"]
    report_id: ReportId
    data: T


class ChurnEvaluationResponse(ServiceMetadata, EvaluationScope):
    model: ChurnModelCard
    provenance: Provenance
    metrics: ChurnMetrics


class ClvEvaluationResponse(ServiceMetadata, EvaluationScope):
    model: ClvModelCard
    provenance: Provenance
    metrics: ClvMetrics


class LimitationsResponse(ServiceMetadata):
    model: ModelCard
    limitations: Annotated[tuple[Limitation, ...], Field(min_length=1, max_length=12)]


class ChurnExplainabilityResponse(ServiceMetadata, ExplanationData):
    model: ChurnModelCard
    provenance: Provenance
    interpretation: Literal["model-association"]
    causal: Literal[False]


class ClvExplainabilityResponse(ServiceMetadata, ExplanationData):
    model: ClvModelCard
    provenance: Provenance
    interpretation: Literal["model-association"]
    causal: Literal[False]


class SegmentationResponse(ServiceMetadata, SegmentationData):
    provenance: Provenance


def _nested_model_id(value: object) -> str | None:
    model = value.get("model") if isinstance(value, dict) else getattr(value, "model", None)
    tag = model.get("model_id") if isinstance(model, dict) else getattr(model, "model_id", None)
    return tag if isinstance(tag, str) else None


type EvaluationResponse = Annotated[
    Annotated[ChurnEvaluationResponse, Tag("churn")] | Annotated[ClvEvaluationResponse, Tag("clv")],
    Discriminator(_nested_model_id),
]
type ExplainabilityResponse = Annotated[
    Annotated[ChurnExplainabilityResponse, Tag("churn")]
    | Annotated[ClvExplainabilityResponse, Tag("clv")],
    Discriminator(_nested_model_id),
]
