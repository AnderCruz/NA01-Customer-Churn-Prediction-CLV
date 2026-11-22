# Phase 10 API architecture and contracts

**Document ID** · NCI-API-001\
**Version** · 0.2\
**Status** · Phase 10 accepted and completed with documented limitations\
**Work package** · WP-10.10, Final Engineering Audit

## Authority and baseline

Gate 01 was verified on `main` in `AnderCruz/Customer-Churn-Prediction-CLV`.
Local HEAD, recorded `origin/main` and live GitHub `main` agreed at
`a2095f8ff64fd6af52ee466c23a774a81e686f8a`. The accepted Phase 09 commit
`74eb4a407b97ba0025c32ced0048a1ff049064d9` remains its ancestor and has
the same tree. Local notebook execution outputs were backed up outside Git
and the two working copies were restored from HEAD with owner authorisation.
WP-10.2 reverified the same local and live refs, the clean index and the
expected unstaged WP-10.1 roadmap and specification. Both accepted notebooks
matched HEAD. The Project Owner approved API-PO-001–005 on 21 November 2026.
That approval fixed the architecture and scope for the subsequent implementation increments.

NEDS v1.1 sections 10, 12, 14–16 and 21 govern testing, Python API design, security,
Git and documentation. ADR-001–004 bind the modular-monolith, local-first,
client-isolation and CSV decisions. ADR-009 and ADR-010 bind episode grain
and canonical identity. The approved Customer Data Contract v1.1 governs
CSV intake. ORCH-001–014 govern existing Python orchestration. Accepted
Phase 05–09 records govern what evidence and claims may be reused.
The FR, NFR, MVP acceptance, system architecture, MVP technical design and
deployment documents provide traceable baseline proposals. Their draft
status matters, including proposed storage and deployment technologies.
The complete standalone approved roadmap and Charter were unavailable.
Phase order follows the owner brief and repository alignment. [ADRs](../03_architecture/architecture_decisions.md),
[ADR-010](../03_architecture/adr_episode_identity_and_identifier_management.md),
[Customer Data Contract](../04_data/customer_data_contract.md),
[Orchestration](../03_architecture/pipeline_orchestration_specification.md),
[System Architecture](../03_architecture/system_architecture.md),
[MVP Technical Design](../03_architecture/mvp_architecture_and_technical_design.md),
[Approval Register](../07_project_management/documentation_review_and_approval.md),
[Deployment and MLOps](deployment_and_mlops_strategy.md),
[Roadmap](../07_project_management/implementation_plan_and_roadmap.md).

## Purpose and exposure

The approved Nowa Customer Intelligence Internal Research & Analytics API is a
read-only internal interface for engineers, reviewers and controlled
demonstrations using authorised synthetic research. Intended consumers
can inspect capability availability, model cards, evaluation summaries,
explanation summaries and RFM research status. Phase 11 owns dashboard
development. The initial API uses one fictional Fieldwise Cloud audience
and a curated allowlist of released aggregates. Accessible data consists
of approved definitions, bounded aggregate summaries and provenance
references. Customer-level cases, source files, Registry mappings,
unrestricted reports and protected reserves are excluded.

Individual or batch churn scoring, risk bands, customer recommendations,
operational segmentation, commercial CLV and revenue-at-risk are outside
the authorised research scope. An operational service requires approved
client-specific eligibility and model performance, identity and tenant
controls, privacy and security review, retention and audit, monitored model
promotion, incident response and commercial acceptance. A functioning
research interface does not meet those release criteria.

### Phase 11 integration boundary

The approved primary dashboard platform is Microsoft Power BI. The proposed
initial integration uses verified analytical datasets prepared in Python,
with Power Query for dashboard data preparation and DAX for analytical
measures in the Power BI semantic model. DASH-PO-001 and DASH-PO-002 approve
the platform and this separation of responsibilities. DASH-PO-003 allows
the dataset boundary without a mandatory FastAPI runtime dependency.
DASH-PO-004 limits initial dashboards to authorised synthetic evidence and
preserves the accepted research limitations. Dashboard outputs cannot be
presented as validated commercial predictions. The nine approved GET
contracts and API-PO-001 through API-PO-005 govern WP-10.2. A Power BI-specific
endpoint would require separate approval. Phase 11 implementation remains
pending.
[Approved dashboard technology direction](../07_project_management/implementation_plan_and_roadmap.md#24-phase-11-dashboard-development).

## Current component inventory

Module paths below start at `nowa_customer_intelligence`. Dependencies
are the material boundaries an adapter would inherit. The first API
would use only the report and contract metadata interfaces.

| Component and Python interface | Input → output and dependencies | Maturity, reuse and limits |
|---|---|---|
| `data.ingestion.header_inspection.inspect_csv_header` and `data.ingestion.csv_ingestion.ingest_csv_dataset / ingest_client_datasets` | Documented CSV path and dataset or directory → headers and raw Pandas frames. Requires approved templates and local files. | Implemented local intake. Keep separate from HTTP. File paths and uploaded client data remain out of scope. |
| `data.preprocessing.type_normalization.normalize_dataset_types / normalize_client_datasets` and `data.schemas` | Raw frames → normalised typed frames and dataset-specific Pandera validation. Uses the five CSV schema contracts and Pandas/Pandera. | Implemented pipeline stages, reusable offline. HTTP payloads require dedicated response DTOs. |
| `data.validation.validator.validate_data_quality` and `pipeline.execution.execute_pipeline` | Validated dataset mapping with RI findings → quality report. Explicit `PipelineExecutionRequest` → outcomes and PES. Uses schema, RI, temporal checks and approved BASIC/TEMPORAL discovery. | Implemented technical orchestration. RI checks key existence. Registry consistency and semantic attribution remain unimplemented where required by client orchestration. No run endpoint. |
| `data.synthetic.identity_registry.EpisodeIdentityRegistry.lookup / verify_many / allocate_many / correct_source_key / history` | Local SQLite and client/namespace-qualified synthetic episode identity → UUID mapping, consistency, correction history. Uses the approved key shape and transaction boundary. | Implemented for the fictional generator. Reuse as reference for future client identity architecture. Neither customer/account keys nor supplied episode UUIDs confer authority. No Registry API. |
| `data.synthetic.observations.validate_usage / validate_snapshots` and `data.synthetic.historical_features.build_historical_features` | Timestamped fictional evidence → coverage and as-known historical scope. Requires accepted event, snapshot and availability rules. | Development evidence interfaces. Missing and not-yet-available records are distinct from observed zero activity. No direct API exposure. |
| `data.synthetic.feature_matrix.FEATURE_SPECS / extract_feature_row / build_feature_matrix` and `data.synthetic.feature_exports.write_feature_bundle` | Episode with linked canonical account, UTC observation and permitted history → 25 ordered predictors, prediction eligibility and optional distinct outcome ledger. Bundle writes manifest and digests. | Accepted Phase 05 synthetic workflow. Reuse registry descriptions only. Retrospective outcomes do not authorise predictor rows or leak into features. |
| `models.churn.dataset.load_bundle / partition / model_inputs`, `models.churn.estimators.churn_scores` and `models.churn.research.load_reports` | Verified development bundle or frozen ordered frame → partition/features or class-1 scores. Report loader returns checksum-verified paired baseline and advanced JSON. Uses sklearn, Pandas and retained experiment evidence. | Phase 06 experimental 30-day episode prediction. Use aggregate report projections. The frozen model and threshold `0.003965284793899528` are research-only. AP ≈0.01138, ROC-AUC ≈0.23272, eight positive validation accounts and 695 false positives. The seed-2027 holdout is unscored. |
| `models.clv.history.historical_value`, `models.clv.features.FEATURES / customer_features`, `models.clv.research.model_inputs / load_report` and `explainability.frozen.FrozenModel.predict` | Time-bounded synthetic account ledger → history snapshot and 17 ordered raw features; verified report JSON → retained research results. Frozen wrapper uses sklearn pipeline and clips final GBP to zero. | Accepted experimental billed value. Reuse report loader and field definitions. `load_development` also loads a trusted binary and rebuilds development cohorts, placing it outside the metadata service. |
| `models.segmentation.profiles.profile_accounts`, `models.segmentation.rfm.fit_references` and `models.segmentation.research.load_report` | As-known account history → deterministic RFM profiles and boundaries. Verified protocol, design and report files → research status. Uses history rules, frozen reference support and local JSON. | Accepted descriptive methodology. Tie groups and cadence checks matter. No cluster nominee, no operational assignments, no reserve score. Project only aggregate research status. |
| `explainability.frozen.feature_lineage`, `explainability.methods.grouped_shapley` and `explainability.research.load_report` | Fitted transformation positions → raw-feature lineage. Predictor, rows, training background and blocks → experimental attributions. Verified report JSON and protocol → retained research evidence. Uses Pandas/NumPy, sklearn and SHAP in isolated research where needed. | Phase 09 engineering and research accepted. The API reads projected aggregates only. Churn probability and log odds have separate scales. CLV uses model-agnostic four-block attribution in clipped issued GBP. Local cases, row evidence, attribution generation and causal claims are excluded. |

The `api/README.md` is a historical placeholder. The Python package contains
no ASGI app, HTTP router, application auth, response contracts, evidence
projection adapter or API-specific CI. [API placeholder](../../api/README.md),
[Pipeline source](../../src/nowa_customer_intelligence/pipeline/execution.py),
[Phase 05](../07_project_management/implementation_plan_and_roadmap.md#18-phase-05-point-in-time-feature-engineering),
[Phase 06](../05_ml/phase06_churn_evaluation_protocol.md),
[Phase 07](../05_ml/phase07_clv_economic_definition_and_validation.md),
[Phase 08](../05_ml/phase08_segmentation_scope_and_validation.md),
[Phase 09](../05_ml/phase09_explainability_scope_and_validation.md).

## Requirements reconciliation

Priorities below retain the original draft FR classifications. An
unmet Must remains an eventual MVP release blocker unless the owner
explicitly revises scope. The five approved API-PO decisions govern the research API only.
In the matrix, Phase 10 API uses were verified against isolated synthetic fixtures.
Rows retained offline, deferred, or blocked are not counted as addressed. [FR baseline](../02_requirements/functional_requirements.md),
[NFR baseline](../02_requirements/non_functional_requirements.md),
[MVP acceptance](../02_requirements/acceptance_criteria.md).

| FR and original requirement | Priority | Evidence and restriction | Approved research treatment and deferred release decision |
|---|---|---|---|
| 001–006, CSV intake, schema and quality | Must each | Local CSV and technical DQ implemented. Client identity and eligibility need more than CSV validity. | Reuse internally, no HTTP ingestion. 001–006 retain existing acceptance scope. |
| 007, source lineage / 008, API ingestion | Should / Could | Local manifests and PES exist. | Expose released report provenance under PO-004. Defer uploads to separate ingestion approval. |
| 009–010, historical/tenure features / 011, payment and usage / 012, point-in-time / 013, feature versioning | Must, Must, Should, Must, Should | Frozen Phase 05 episode registry and separate account-level CLV registry. Missing coverage remains explicit. | Metadata only under PO-004. Operational availability and feature assembly remain separate gates. |
| 014, baseline churn evaluation | Must | Phase 06 development evaluation retained. Reserve unscored. | Report scope and limitations under PO-004. Full MVP holdout criterion remains open. |
| 015, eligible churn probability | Must | Frozen episode prediction callable exists. Weak ranking and low event support. | Evaluation only under PO-001/004. New predictive, eligibility and release approval required. |
| 016, configurable risk bands | Must | Fixed development threshold is experimental. No approved calibration or operational thresholds. | No risk bands. New validation and owner approval required. |
| 017, batch scoring | Must | Development scoring interfaces and reports only. | Defer scoring transport and release. Requires accepted eligibility, validated model and approved batch policy. |
| 018, persist timestamp and model version per score | Must | Provenance exists for research runs. No released scoring result store. | Expose evidence version and experiment timestamps under PO-004. Per-result traceability remains a blocker. |
| 019, authenticated individual scoring API | Should | No authenticated serving or approved operational predictor. | Defer. Separate synthetic-only CLV option needs explicit approval. |
| 020, historical prediction snapshots | Should | Retained experimental results exist outside Git. | Defer operational prediction history and retention policy. |
| 021, historical customer revenue | Must | Phase 07 history measures issued GBP subject to coverage. | Include only allowed aggregate definitions under PO-004. No equivalence to revenue recognition. |
| 022, future value | Must | Phase 07 estimates six-month issued GBP on fictional accounts. | Evaluation summary under PO-004. Commercial inference needs independent acceptance. |
| 023, value basis | Must | The approved proxy measures gross issuance. | Publish value basis, currency and exclusions under PO-004. Preserve original revenue/margin requirement for eventual release. |
| 024, assumptions, horizon and limitations | Must | Frozen Phase 07 protocol records them. | Include in card and limitations under PO-004. |
| 025, customer-level and aggregate CLV views | Should | Retained development cohorts and case results. | Aggregate research evaluation only under PO-001/004. Defer individual views. |
| 026, customer segments | Must | Deterministic research RFM. No nominated clustering model. | Report non-nomination and methodology. Operational assignment needs separate acceptance. |
| 027, segment sizes and profiles | Must | Bounded descriptive research exists. | Allow approved broad aggregates under PO-004. Preserve operational gap. |
| 028, reviewed configurable labels | Should | No approved operational labels. | Defer until separately nominated and reviewed. |
| 029, expected value at risk | Must | Churn and billed-value models have different grains and horizons. | Release blocker. Requires aligned, defensible exposure design and owner approval. |
| 030, aggregate and segment risk summaries | Must | Neither exposure nor operational segments approved. | Defer with 029. |
| 031, distinguish exposure and recoverable revenue | Must | Governance distinguishes the concepts. No accepted exposure calculation. | Describe capability as excluded. Approve definitions before any release. |
| 032, global importance | Must | Verified Phase 09 research methods and summaries. | Approved aggregates only under PO-004. |
| 033, supported local explanations | Must | Retained research cases exist. | Describe method and limitations under PO-001/004. Defer customer-level delivery. |
| 034, associations and causal boundary | Must | Phase 09 explicitly limits interpretation. | Required labelling and contract tests under PO-004/005. |
| 035–038, 040, dashboard views and filters | Must for 035–038, Should for 040 | Operational churn, commercial CLV, segments and risk remain restricted. | Phase 11 is separate. Reconcile product screens against approved evidence before release. |
| 039, dashboard metadata / 041, scored-result export | Must / Should | Report evidence is available. Scored export lacks operational approval. | Metadata contract can support Phase 11. Exports deferred. |
| 042, ingestion and scoring run records | Must | PES and research manifests exist. No operational scoring audit store. | Bounded API access audit under PO-003/005. Full scoring traceability remains open. |
| 043, model version per prediction | Must | Frozen model identity and fingerprint available. | Carry identity in all model evidence under PO-004. No scoring claim. |
| 044, deployed role access | Should | Client isolation is a design principle. No API auth exists. | Test local research permission boundary under PO-003. Deployed roles require approval. |
| 045, minimise direct identifiers | Must | Canonical identity exists internally. | Exclude raw IDs and row evidence at adapter and schema boundaries under PO-003/004. |

The NFR baseline records objectives and requirements without Must/Should
rankings. The table preserves that classification.

| NFR | Current status and approved research treatment |
|---|---|
| 001–004, throughput, scoring latency, dashboard and long jobs | Untested API targets. No scoring/jobs here. NFR-002 is conditional on approved scoring. Future batch/dashboard requirements remain. |
| 005–008, modularity, scale, configuration and artefact isolation | Accepted modularity/isolation principles and local modular code. Approve an explicit single-audience configuration and scope, with future client isolation tests before a client pilot. |
| 009–015, transport, storage, secrets, least privilege, log redaction, retention and audit | No deployed API controls verified. PO-003/005 require in-process or loopback controls, fail-closed auth, bounded audited events and no customer data. Shared or deployed environments require TLS, access review, secrets/retention and storage controls. |
| 016–020, validation, structured logs, scoring traceability, safe errors and recovery | Local validation and research-run provenance exist. Proposed API errors, logging and readiness require tests. Operational run status and recovery remain future release gates. |
| 021–026, code quality, tests, CI and reproducibility | Local pytest and Ruff with source layout, accepted research fingerprints. PO-004/005 need HTTP contract/lifespan tests, dependency matrix and an API-enabled CI job. |
| 027–032, holdout, imbalanced metrics, calibration, limitations, drift and human review | Preserve verified evaluation partitions and limitations. No operational calibration, drift programme or consequence authorisation established. API reads approved metrics only. |
| 033–036, labels, bands, chart context and accessibility | Standardise API units/definitions. Dashboard presentation belongs to Phase 11. Operational bands remain excluded. |

For MVP acceptance, AC-001–004 retain offline ingestion, validation, quality
and leakage evidence. AC-005–006 retain historical evaluation and expose
approved metrics with their partition. AC-005's unscored holdout remains an
open criterion. AC-007–008 require operational batch and per-result
traceability. AC-009 is supported only for the issued-GBP proxy. AC-010
has descriptive research evidence and no operational model. AC-011 remains
open. AC-012 has accepted research evidence and no consumer-facing local
delivery. AC-013/014/016 remain dashboard, export and packaging work.
API tests and docs contribute to AC-015/017/018 after verification.

| Phase 10 disposition | Traceable examples and required verification |
|---|---|
| Addressed in contract, pending implementation | FR-024/032/034/045, unit and proxy disclosures, aggregate explanation governance and identity minimisation. Verify through CT-01/06, API-10/12/14 and AC-018. |
| Partial research evidence | FR-018/022/023/025/027/033/042/043, provenance, aggregate billed-value claims and local-explanation restrictions. Preserve open per-score traceability, economic, operational profile and local result delivery obligations. Verify API-07/09–12. |
| Blocked for operational release | FR-015/016/017, weak churn validation, no approved calibration or batch eligibility. FR-026/028, no approved segmentation nominee. FR-029–031, no defensible exposure design. Each requires separate evidence and owner approval. AC-005/007/008/010/011 stay open for operational scope. |
| Deferred or outside this API | FR-008/019/020/041, uploads, scoring, prediction history and scored export. NFR-009/010/014/020 and FR-044 need separate owner approval for deployed transport, storage, retention, recovery and shared roles. NFR-002 remains an unmeasured scoring target. |

## Application structure and dependencies

Keep a FastAPI application factory inside `src/nowa_customer_intelligence/api`
with `application.py` (lifespan, routing, exception mapping and dependency
wiring), `configuration.py` (strict startup settings and validated loopback
launcher), `contracts.py` (closed Pydantic v2 DTOs), `routes.py` (health and
research router), and `research.py` (verified immutable catalogue).
Split auth or error handling into additional files only when warranted by
a concrete boundary. Reuse domain definitions and existing evidence-reader
semantics. Keep runtime transport independent of modelling and Pandas.

The request order is transport ceilings and local host checks, generated
request ID, authentication and scope, request shape, catalogue readiness,
resource lookup, typed response and redacted audit event. Create the safe
request ID before emitting any error from the application. Enforce the local
host and authority at the boundary, then reject malformed resource requests
before reporting resource state. Initialise evidence within lifespan, never
by a first-request side effect.

The project Python is 3.12.3 and Pydantic is 2.14.3. FastAPI, Starlette,
Uvicorn, HTTPX and HTTPX2 are absent from the main environment. The current
`api` extra declares `fastapi>=0.115,<1.0` and
`uvicorn[standard]>=0.30,<1.0`. The standard regression job installs
`dev,notebooks`. The separate API job installs `api,api-test` and uses
the verified application dependency versions.
WP-10.2 used a temporary Python 3.12.3 environment and verified this minimal
set with `pip check` and an offline disposable ASGI app.

| Dependency | Verified version and role |
|---|---|
| FastAPI / Starlette | 0.165.0 / 1.10.0. ASGI lifespan, dependency injection and OpenAPI. Starlette remains transitive. |
| Pydantic / pydantic-core | 2.14.3 / 2.50.4. Strict response validation and JSON serialization. Pydantic remains a base dependency. |
| Uvicorn | 0.54.0, plain distribution. Configuration import and loopback settings verified without binding. |
| HTTPX2 | 2.16.2. In-process TestClient transport. Classic HTTPX 0.28.1 raised a Starlette deprecation warning. The successful probe used HTTPX2 alone. |

The disposable smoke verified lifespan startup/shutdown, unauthenticated
and invalid-input statuses, strict field types, non-finite and unexpected
field rejection, decimal JSON strings and machine-readable bearer OpenAPI.
It did not implement any Nowa route or measure networking performance.
For a repeat of the minimal WP-10.2 matrix in WP-10.3, use a fresh API
environment. Add a bounded implementation constraint set and a dedicated
CI API test job during later approved changes. The proposed direct addition
to the project is `api-test = ["httpx2==2.16.2"]` in optional dependencies.
Retain the existing runtime ranges and record the validated versions in
the implementation constraints. The optional Uvicorn extras declared by
the project need verification in the eventual project/API CI environment.
No dependency or CI declarations changed in WP-10.2.

```bash
python3.12 -m venv /tmp/nci-api-foundation
/tmp/nci-api-foundation/bin/python -m pip install \
  fastapi==0.165.0 starlette==1.10.0 uvicorn==0.54.0 \
  pydantic==2.14.3 httpx2==2.16.2
/tmp/nci-api-foundation/bin/python -m pip check
```

[Declared dependencies](../../pyproject.toml), [CI](../../.github/workflows/ci.yml),
[FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/),
[Starlette TestClient](https://starlette.dev/testclient/).

### WP-10.3 application foundation

The implemented package contains the application factory and ASGI lifespan
in `api/application.py`, strict Pydantic settings in `api/configuration.py`,
typed state and catalogue injection in `api/dependencies.py`, and stable
error envelopes in `api/errors.py`. `api/__init__.py` identifies the package.
The future route, response-contract and evidence-reader modules remain
separate implementation increments.

`create_app(configuration=None, *, catalogue_lifespan=None)` defaults to
validated in-process settings. Callers can explicitly use
`ApiConfiguration.from_environment(mapping)` for the approved
`NCI_API_` namespace. Construction does not read environment variables
implicitly, open research files, load models or bind a socket. Service
identity exposes the approved title, contract version `1.0.0` and Python
package build version. The response schema and route versioning remain
as approved below.

Loopback settings accept only `127.0.0.1` or `::1` and require a paired
absolute bundle root and SHA-256 pin, a valid-format bearer secret and
bounded UTC expiry. Configuration errors are sanitised and the bearer
secret is excluded from display and serialization. An expired secret
prevents lifespan startup before any dependency acquisition. This proves
configuration validation and the absence of a listener in this foundation.
Actual bind and Host enforcement, credential authentication, scoped
authorisation and transport limits must land with the controlled launcher
and applicable routes before any HTTP demonstration.

Each application owns its own immutable foundation state. An injected
asynchronous context manager accepts settings and can publish a trusted
catalogue handle for its lifetime or yield `None` when evidence is
unavailable. The default yields `None` and reads no evidence. The
catalogue dependency raises `EVIDENCE_UNAVAILABLE` without usable state.
Startup and shutdown failures produce sanitised lifecycle errors and
restore the initial state. No readiness route or verified evidence loader
exists yet.

The foundation emits the v1 `ApiError` shape, a generated UUID4 request
ID and `Cache-Control: no-store` on handled responses. It maps expected,
framework validation and internal failures to bounded messages. The
request boundary consumes unexpected exceptions before server propagation.
The factory ships without health or research endpoints and disables
Swagger UI, ReDoc, HTTP OpenAPI and slash redirects. A local Python
`app.openapi()` call is available for contract development. Route-specific
errors, transport ceilings and structured audit events remain deferred.

The main environment and project dependency declarations were left
unchanged. Tests in the isolated Python 3.12.3 environment used FastAPI
0.165.0, Starlette 1.10.0, Pydantic 2.14.3, Uvicorn 0.54.0, HTTPX2 2.16.2
and pytest 8.4.2. At WP-10.3 the standard CI environment omitted the API extra.
WP-10.8 added the dedicated `api-contracts` job. Use the isolated environment above and run
`python -m pytest -q -W error tests/unit/api tests/integration/test_api_foundation.py`
with pytest installed. The dedicated CI job now installs `.[api,api-test]` with the verified versions.

[Factory](../../src/nowa_customer_intelligence/api/application.py),
[settings](../../src/nowa_customer_intelligence/api/configuration.py),
[application dependencies](../../src/nowa_customer_intelligence/api/dependencies.py),
[error contract](../../src/nowa_customer_intelligence/api/errors.py),
[offline ASGI tests](../../tests/integration/test_api_foundation.py),
[configuration tests](../../tests/unit/api/test_configuration.py).

#### WP-10.3 acceptance checklist

| ID | Result | Verified foundation evidence |
|---|---|---|
| FND-01 | Passed | Independent FastAPI factories expose the approved service identity. |
| FND-02 | Passed | API package added in the existing modular monolith. Data, feature and model packages remain unchanged. |
| FND-03 | Passed | Strict typed settings parse the approved environment namespace explicitly. |
| FND-04 | Passed | Missing credentials, invalid expiry, incomplete pins and unsafe settings reject construction or startup. |
| FND-05 | Passed | Default execution and ASGI tests run in-process. |
| FND-06 | Passed for foundation | Both valid modes construct no listener and publish no routes. Public bind configuration is rejected. A controlled launcher and request-level enforcement remain release gates. |
| FND-07 | Passed | Lifespan starts and stops injected dependencies and restores state on exit or failure. |
| FND-08 | Passed | Fixture, missing and unavailable catalogue cases are testable through explicit injection. |
| FND-09 | Passed for foundation | Stable error IDs and request IDs are verified against sanitised HTTP and lifespan failures. Endpoint-specific errors and audit logging remain later work. |
| FND-10 | Passed | No operational scoring endpoints or other business routes are registered. |
| FND-11 | Passed | The factory imports no modelling stack and performs no request-time research. |
| FND-12 | Passed | 51 offline foundation tests passed with warnings treated as errors. |
| FND-13 | Passed | Repository-wide Ruff lint and formatting passed. |
| FND-14 | Passed within execution scope | 1,092 existing regression tests passed. Model fitting and scoring collections, research notebook replay and the separate foundation suite were excluded from this run. |
| FND-15 | Passed | 40 non-reserve inputs and four Phase 09 report fingerprints matched. Accepted notebook blobs were unchanged. |
| FND-16 | Passed | Changes are limited to the foundation, tests and Phase 10 documentation. Phase 11 remains pending, and no Git history changes were made. |

## Approved service contracts

The API title is **Nowa Customer Intelligence — Internal Research & Analytics API**.
The contract version is `1.0.0`, with seven `/v1` research routes and two
unversioned health routes. All nine operations use GET. Requests have no body
and accept no query parameters. Model routes require one path parameter
`model_id`, an ASCII slug matching `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`,
1–48 characters. Only `churn` and `clv` resolve. Extra query fields, an empty
value or an invalid slug give 422 when the router matches the path. A missing
path segment follows normal route matching, including the model-list route.
Reject unexpected bodies with 400 and enforce the transport limits below.
There is no client-supplied audience or client selector.

Return JSON with `X-Request-ID`. Set `Cache-Control: no-store` on all API
responses, including errors. Store bounded validated response objects in the
process for steady-state lookup. Responses are ordered deterministically
by the release contract. Health routes require loopback or the in-process
boundary and need no credential. All research routes require the fixed
audience `fieldwise-fictional` and scope `research:read` before release or
model lookup. This gives a valid caller 404 for an unknown model when the
catalogue is ready. A caller without access receives the access error
regardless of the model ID. A missing catalogue returns 503 before model
resolution. No individual or batch scoring, customer lookups, Registry
writes, RFM assignments, live explanations or risk decisions are exposed.

The table defines operation IDs, request and response schemas, provenance,
size ceilings, and minimum route-specific tests. Research success payloads
use the named DTOs directly with a common metadata base. Common research
errors are 401, 403, 422, 503 and 500. Common transport errors are
400, 405, 413, 414 and 431, where applicable. The 404 marked on model
operations is in addition to the common research errors. Status 405 includes
`Allow: GET` for a recognised read-only resource. Unregistered paths and
excluded capabilities have no route and return 404. If a registered
operation is withdrawn by permission policy, authorised authentication
alone cannot bypass the 403.

For requests that reach ASGI, validate transport limits and local authority
before access checks. On a recognised research route, authenticate and
authorise before reporting invalid parameters, catalogue state or model
existence. Once authorised, validate parameters before readiness, then
resolve the model. On health routes, validate the empty request before
checking status. A host outside the configured local authority receives a
generic 400. Liveness has no evidence-dependent 503. Health can return
422 for an unexpected query and 500 for an internal failure, with the
same safe error envelope as research routes.

| GET path / operation ID | Request and response | Auth, evidence and specific tests |
|---|---|---|
| `/health/live` / `getLiveness` | Empty. 200 `LivenessResponse`, up to 1 KiB. | Boundary only. No evidence lookup. Empty or failed catalogue still returns live. |
| `/health/ready` / `getReadiness` | Empty. 200 `ReadinessResponse` or 503 `ApiError`, up to 1 KiB. | Boundary only. Checks published state. Test atomic publication, missing/digest/schema failure and no internal details. |
| `/v1/research/capabilities` / `listResearchCapabilities` | Empty. 200 `CapabilitiesResponse`, up to 4 KiB. | Research scope. Configuration and pinned release. Test exact capability IDs, service version and approved availability only. |
| `/v1/research/models` / `listResearchModels` | Empty. 200 `ModelListResponse`, up to 16 KiB. | Research scope. Both verified model metadata entries. Test stable order `churn`, `clv` and no synthetic row data. |
| `/v1/research/models/{model_id}` / `getResearchModel` | Slug. 200 `ModelResponse` or 404, up to 8 KiB. | Research scope. Selected verified Phase 06 or 07 card. Test model identity, target and version. |
| `/v1/research/models/{model_id}/evaluation` / `getResearchEvaluation` | Slug. 200 `EvaluationResponse` or 404, up to 16 KiB. | Research scope. Released development-validation summary for the selected model. Test counts, units, evaluation partitions and no reserve fields. |
| `/v1/research/models/{model_id}/limitations` / `getResearchLimitations` | Slug. 200 `LimitationsResponse` or 404, up to 8 KiB. | Research scope. Reviewed model limitations in the pinned release. Test mandatory limitation codes for each model. |
| `/v1/research/models/{model_id}/explainability` / `getResearchExplainability` | Slug. 200 `ExplainabilityResponse` or 404, up to 16 KiB. | Research scope. Released Phase 09 aggregates linked to the same model fingerprint. Test method/scale, support and exclusion of row-level or local case details. |
| `/v1/research/segmentation/status` / `getResearchSegmentationStatus` | Empty. 200 `SegmentationResponse`, up to 8 KiB. | Research scope. Released Phase 08 RFM status. Test negative nomination and no cluster ID, customer ID or assignment. |

Apply CT-01, CT-02, CT-06 and CT-07 to every operation. Apply CT-03 and
CT-04 to every research operation before enabling its route. Apply CT-05 to
readiness and all catalogue-backed routes, including capabilities. CT-08
measures the nine released routes without scoring. The two health routes
have no API version prefix or research envelope. All seven research success
responses carry the v1 metadata below.

### Pydantic v2 DTO specification

Implement explicit `BaseModel` subclasses consistent with project conventions
and `ConfigDict(strict=True, extra="forbid", frozen=True, allow_inf_nan=False)`
for response models. Use immutable nested DTOs and tuples internally, with
tuples represented as arrays in JSON and OpenAPI. Validate source-to-DTO
conversions explicitly before publication. Structural settings and numeric
fields receive no implicit string-to-number or bool-to-number coercion.
Use `Literal` or string enums for finite vocabularies and verify valid
wire values. Field names are snake_case. All fields below are required and
non-null unless marked **omittable** or **nullable**. Omit absent optional
fields. Use explicit null only on specified nullable fields and pair it
with a reason. Reject non-finite values in the pinned release and the
response. Unknown information is neither zero nor fabricated.

| Primitive | Input and wire contract |
|---|---|
| `Slug`, `Digest`, `SafeText` | Slug as above, SHA-256 as 64 lowercase hex characters, safe text of 1–240 Unicode characters without control characters. Public reason text comes from reviewed copy, never from exceptions. |
| `Count`, `Finite`, `Fraction` | Integer 0–2,147,483,647, finite JSON number, and finite JSON number in [0,1], respectively. Attribution absolute values and residuals are non-negative. Signed bias, R² and rank correlation may be negative. |
| `Gbp` | Internally `Decimal` from an approved decimal string or precise decimal JSON parse. On the wire a base-ten string without a sign unless the metric permits signed values, without exponent notation, with exactly two fractional digits and at most 12 integer digits. Convert CLV evaluation display values explicitly to pennies using decimal half-even rounding. Reconciliation errors and attribution magnitudes retain finite numerical precision and do not use the penny display type. |
| `UtcInstant` | UTC-aware datetime, RFC 3339 strings with `Z` on the wire. Validate actual calendar/time values and reject naive datetimes. Never infer a timestamp from a report filename or mtime. |

| DTO | Required fields, type and cardinality |
|---|---|
| `LivenessResponse` / `ReadinessResponse` | `status` literal `live` or `ready` respectively. Failed readiness uses the safe 503 envelope below. |
| `ServiceMetadata` | `api_version` literal `v1`, bounded `service_version` derived from package build metadata, `schema_version` literal integer `1` and `evidence_version` (`Slug` release ID). Inherit these four fields on all success research response classes. |
| `Provenance` | `report_id` (one of the five IDs in the evidence table), `experiment_id` (the exact associated protocol), `report_schema_version` (`Slug` agreed release DTO schema ID), `report_sha256` (`Digest` of the projected report), `audited_commit` (40 lowercase hexadecimal characters). `source_report_sha256` (`Digest`, supplied in the reviewed release) identifies the retained source only. `feature_contract_version` (`Slug`) is omittable for segmentation, mandatory for model evidence. `published_at` (`UtcInstant`) is omittable when no release timestamp was recorded. |
| `ResearchCapability` / `CapabilitiesResponse` | `capability_id` literal `models`, `evaluation`, `limitations`, `explainability` or `segmentation-status` and `status` literal `available`. Response adds `capabilities`, a fixed five-entry tuple with one of each in the listed order. Unapproved capabilities have no entries. |
| `ModelCard` / `ModelResponse` / `ModelListResponse` | `model_id` literal `churn` or `clv`, `display_name` and `model_family` from the released identity table, `model_version` (model fingerprint `Digest`), `entity`, `target`, `horizon_value`, `horizon_unit`, `prediction_unit`, `data_origin` literal `fieldwise-fictional`, `evaluation_status` literal `experimental-development-validation`, `production_approved` literal `false`, `limitation_ids` (mandatory codes below, max 12) and `provenance`. The responses add `model` or `models` (exactly two distinct model cards). |
| `EvaluationResponse` | `model`, `provenance` for its evaluation, `partition` literal `development-validation`, `observations` and `accounts` (`Count`, with 1 ≤ accounts ≤ observations). One typed `metrics` variant determined by `model.model_id`. Churn fields `average_precision`, `roc_auc`, `precision`, `recall`, `brier` and `research_threshold` (`Fraction`), and `positive_accounts`, `false_positives` (`Count`). CLV fields `mae_gbp`, `rmse_gbp`, `median_ae_gbp`, `signed_bias_gbp` (`Gbp`, signed only for bias) and `r2` (`Finite` ≤1, nullable). `r2_unavailable_reason` is required with null R² and absent otherwise, literal `undefined` or `not-released`. |
| `Limitation` / `LimitationsResponse` | `id` from approved code list, `severity` literal `restriction` or `caution`, `description` (`SafeText`). Response adds `model` and `limitations`, 1–12 unique `Limitation` records whose IDs exactly match the card. |
| `AttributionTerm` / `ExplanationMethod` | `term_id` from the released allowlist, `mean_absolute` finite and ≥0. Method has `method`, `output_scale` and `unit` from the approved combinations below, `training_background_accounts`, `global_validation_accounts`, `reconciled_rows` and `failures` (`Count`), `tolerance` (positive `Finite`), `max_error` (non-negative `Finite`) and `terms` (0–8 `AttributionTerm`). `background_rank_median`, `bootstrap_rank_median` (omittable `Finite` in [−1,1]) are present only for approved primary-scale aggregates. A released method requires zero failures and `max_error≤tolerance`. |
| `ExplainabilityResponse` | `model`, `provenance` for Phase 09, `methods` (2 ordered churn methods or 1 CLV method), `limitation_ids` (2–8 distinct allowed IDs), `interpretation` literal `model-association`, `causal` literal `false`. |
| `SegmentationResponse` | `method` literal `rfm`, `method_version` literal `fieldwise-segmentation-v0`, `data_origin` literal `fieldwise-fictional`, `evaluation_scope` literal `synthetic-development-research`, `nomination` literal `none`, `operational_assignment_available` literal `false`, `dimensions` (exactly `recency`, `frequency`, `monetary` in order), `limitation_ids` (1–8), `provenance`. |
| `ApiError` | `schema_version` literal integer `1`, `request_id` (server-generated lowercase UUID4), `code` from the HTTP table below and `message` (`SafeText`). `issues` (omittable, up to eight `ValidationIssue{field,reason}`). Fields are `model_id`, `query` or `body` and reasons `invalid-format`, `unexpected-field` or `not-allowed`. Never echo caller input. |

### Released research meanings

The public identifiers below are API aliases. Model family and fingerprints
must match the accepted experiments. Do not derive them from an arbitrary
file name or description.

Use separate `ChurnModelCard` and `ClvModelCard` with literal `model_id`
discriminators. Evaluation uses `ChurnEvaluationResponse` and
`ClvEvaluationResponse`, each containing its matching card and typed
metrics model. Explanation responses similarly use
`ChurnExplainabilityResponse` and `ClvExplainabilityResponse`.
Use the same nested card variants for model detail and limitations.
For a union whose selector is nested, dispatch on `model.model_id`
using a callable Pydantic discriminator and explicit tags. Do not add a
redundant top-level field. Validate the generated OpenAPI `oneOf`
representation for type-specific responses. Catalogue `models` is the
ordered pair of the two card variants.

| ID and display name | Frozen family and evidence | Typed model meaning and mandatory limitations |
|---|---|---|
| `churn`, Contractual subscription churn | `HistGradientBoostingClassifier`, `nci-phase06-v1`, `fieldwise-episode-features-v1` | `entity=subscription-episode`, `target=contractual-churn`, `horizon_value=30`, `horizon_unit=day`, `prediction_unit=class-1-probability`. Limitations `synthetic-only`, `weak-churn-validation`, `uncalibrated-for-operational-use`, `no-operational-risk-bands`. The accepted AP ≈0.01138, ROC-AUC ≈0.23272, eight positive validation accounts and 695 false positives are permitted only as experimental context. |
| `clv`, Six-month billed value | `HistGradientBoostingRegressor`, `fieldwise-clv-v1`, 17 raw features under the same version | `entity=customer-account`, `target=future_6m_issued_gbp`, `horizon_value=6`, `horizon_unit=calendar-month`, `prediction_unit=gross-issued-gbp`. Limitations `synthetic-only`, `billed-value-proxy` and `no-operational-use`. Contract text must distinguish gross issuance and clipping from collected cash, recognised or net revenue, profit, contribution margin and discounted lifetime value. Contractual monthly-normalised snapshots have a distinct GBP-per-month unit. |

The accepted `model_version` for churn is
`16d7a588ec36dc4b22beb20b56f98903af68d4453563921985ba063a024a8cd1`.
For CLV it is
`250f4d860a662f69f95e2577cd890dc4f86d75c33771bc8dc0ed04aa4398afc7`.
The release pin governs the specific permitted pair. Cards and all
dependent responses must link to these same model versions.

Churn explanations list `tree-shap-interventional` first at
`class-1-probability` / `probability` and second at `class-1-log-odds` /
`log-odds`. Never sum odds contributions on the probability scale. The
probability terms are `episode_age_days`, `latest_sessions` and
`expected_usage_months`. Leave log-odds terms empty in the initial release.
The CLV method combination is `finite-background-block-shapley` at
`clipped-gross-issued-gbp` / `GBP`, with term IDs `account-lifecycle`,
`invoice-history-and-cadence`, `contract-snapshots` and `calendar`.
Mandatory explainability limitations are `model-behaviour-only`,
`background-dependent` and `no-causal-effects`, plus
`weak-churn-validation` for churn and `correlated-billing-fields` for CLV.
Aggregate stability is descriptive. The interventional CLV TreeSHAP failure
is supporting context, never relabel the accepted group method as TreeSHAP.
Approve no individual explanations. For Phase 08 use the limitation
`no-nominated-clustering-model` and preserve the research-only RFM scope.

### OpenAPI

Use FastAPI's generated OpenAPI document with explicit operation IDs and
tags `Health`, `Research capabilities`, `Research models` and
`Segmentation research`. Show the typed bases, closed model/metric
variants, enum values, required and nullable fields, version/evidence
definitions, allowed statuses and their `ApiError` schema, and safe
synthetic examples. Model routes document the required slug. Declare
`ResearchBearer` as an HTTP bearer scheme without JWT metadata for all
seven research routes, with the required `research:read` policy described
in operation text. Health operations have empty security requirements.
Document `X-Request-ID`, `Cache-Control`, `WWW-Authenticate` for 401 and
`Allow` for 405 where applicable. Do not include raw evidence, paths, or
credentials. Generate OpenAPI offline via `app.openapi()` and compare a
canonical schema snapshot in tests. Disable implicit Swagger UI, ReDoc,
OpenAPI HTTP routes and router redirects. This preserves exactly nine
routes and keeps application auth independent of documentation visibility.
Breaking contract changes require a new major version and migration plan.
Service build, wire schema, experimental model, feature and evidence
versions are independent. [Strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/),
[FastAPI OpenAPI generation](https://fastapi.tiangolo.com/how-to/extending-openapi/).

### Deferred CLV feasibility

A synthetic fixture endpoint remains a future option and requires its own
approval. No POST route, model-input API or fixture scoring is specified
for implementation in WP-10.3–10.10. Continue to use reviewed evaluation
summaries for demonstrations.

## Approved provenance and evidence catalogue

Load a single immutable, read-only release at application lifespan startup.
The application accepts **projected research summaries**, never an arbitrary
retained research report. The release preparation process is a future,
separately controlled operation. It must use the existing readers' integrity
semantics and bind the actual retained source bytes to approved source
fingerprints. The runtime neither opens original research workspaces nor
reads binary, row, notebook or protected reserve assets. The retained report
locations below establish provenance for future authorised projection.

| Required release file / report ID | Approved retained source relative to `data/processed` | Meaning and allowlisted projection |
|---|---|---|
| `churn-evaluation.json` / `churn-evaluation` | `phase06-research/results/advanced.json`, paired baseline and design where required by the reader | `nci-phase06-v1`. Frozen candidate and fingerprint, validation metrics of that candidate, support from `design.support.validation`, frozen threshold, phase-reviewed limitations and model metadata. Exclude holdout/inventory, individual scores, ROC/PR vectors and other candidates. |
| `clv-evaluation.json` / `clv-evaluation` | `phase07-clv-research/results/report.json` and `phase07-clv-research/design.json` | `fieldwise-clv-v1`. Frozen chosen family and fingerprint, `scores[frozen.name].validation` scalar metrics and `design.support.validation` support. Use approved proxy definitions and limitations. Exclude reserve metrics, case and account records, raw predictions and alternative candidate details. |
| `segmentation-status.json` / `segmentation-status` | `phase08-segmentation-research/report.json` with its verified design and protocol | `fieldwise-segmentation-v0`. Negative nomination from `nominee=null` and reviewed RFM dimensions, status and limits. Exclude candidate labels, profiles of small cohorts, internal dates/identity paths and all assignment records. |
| `churn-explainability.json` / `churn-explainability` | `phase09-explainability-research/churn.json` with verified protocol | `phase09-explainability-v1`. Retained model fingerprint, primary probability and raw log-odds reconciliation, `background.accounts`, global validation support, allowlisted terms from `global.mean_absolute` for probability only and aggregate primary stability statistics. |
| `clv-explainability.json` / `clv-explainability` | `phase09-explainability-research/clv.json` with verified protocol | `phase09-explainability-v1`. Retained model fingerprint, `primary.reconciliation`, `background.accounts`, global validation support, four fixed terms from `global.mean_absolute` and aggregate primary stability statistics. |

For both explanation files exclude case values, feature rows, lineages with
unreleased internal fields, individual attributions, model binaries and
arrays. Restrict all published records to DTO allowlists and use confirmed
synthetic-only source scope. Frozen model identity is the full SHA-256 in
the Phase 06/07 frozen records, cross-checked against the Phase 09 `model.sha256`.
Churn's validation population is 717 observations and 205 accounts.
CLV validation consists of 355 observations across 180 accounts.
No live customer release, separately scored reserve summaries, or runtime
comparison computation is approved.

### Trust, schema and startup

Use an operator-supplied `manifest_sha256` from an owner-reviewed release
record outside the bundle and unavailable to the HTTP caller. The configuration
and bundle locations have independent write authorities. The pinned digest
authenticates fixed-name `release.json` independently of anything in the
bundle directory. An adjacent manifest cannot vouch for itself. Log only
the opaque `release_id` after successful publication.

`ReleaseManifestV1` is a closed record with `schema_version=1`,
`release_id`, `audience=fieldwise-fictional`, `audited_commit`, optional
`published_at` and exactly five distinct typed members. Each `ReleaseMember`
has `report_id`, the corresponding exact basename, `experiment_id` from
the table, `schema_id` literal `research-projection-v1`, `sha256` of the
projected bytes, `source_report_sha256` of the retained original and
`size_bytes` (integer 1–64 KiB). The model members carry `model_id`,
`model_version` and `feature_contract_version`, which are absent for
segmentation. The manifest applies one audience and audited checkpoint to
all members. Model identity and feature version in evaluation and XAI
must agree across projections. Deployment staff establish release IDs and
pins separately. WP-10.2 does not create or approve a concrete release pack.

Each projected JSON member has only `schema_id` (literal
`research-projection-v1`), its `report_id` and a typed `data` member.
Dispatch on the exact manifest report ID. Evaluation data contains
`model` (the corresponding card fields except provenance), `partition`,
`observations`, `accounts`, matching typed `metrics` and `limitations`.
Only the CLV metrics can include `r2_unavailable_reason`. An explanation
projection contains `methods` and `limitation_ids`.
Segmentation data contains the status fields without service metadata or
provenance. Reconcile card IDs, limitation codes, model metadata and
report semantics before assembling responses. Health uses process state,
capabilities are a closed contract list, and model descriptions and
limitations use the corresponding released evaluation record. Populate
provenance, evidence version and service version from verified manifest
and service build metadata after validation. No projected member embeds
its own digest or depends on the hash of a response that contains it.

1. Validate trusted process configuration. An invalid mode, unsafe bind,
   absent loopback credential or malformed trusted digest prevents startup.
2. Open the configured absolute read-only root and fixed basenames under it.
   Reject symlinks, path traversal, non-regular files and substituted members.
   Use race-resistant directory-relative reads with no-follow guards and then
   read a bounded byte buffer once. No filename is supplied by a request.
3. Limit `release.json` to 16 KiB and projected records to 64 KiB each
   (336 KiB total including the manifest). Hash each exact buffer before
   JSON parsing. Verify lengths, digests, versions and the complete required
   inventory. Reject duplicate JSON keys, invalid UTF-8, non-finite numbers
   and unexpected fields at every release-schema boundary.
4. Validate typed aggregates, scientific semantics, model correspondence
   and authorisation scope. Check all final wire size ceilings. Publish one
   deeply immutable snapshot only after every check passes. Use tuples and
   a read-only lookup around frozen DTOs. There is no partial readiness.
5. On missing, corrupt, incompatible or unapproved evidence, keep a validly
   configured process live and all research reads unavailable. Record only
   a safe reason category. Readiness returns 503 `SERVICE_UNAVAILABLE`.
   Authorised research returns 503 `EVIDENCE_UNAVAILABLE` with the same
   public behaviour for each evidence failure.
   Unknown IDs in otherwise valid ready requests return 404. Do not fall
   back to a previous release, a test fixture or a frozen predictor.
6. Run every request from the snapshot. No request-time filesystem refresh,
   scoring, fitting or Registry access. A controlled restart is the only
   release refresh. This trades hot updates for bounded latency and a
   single verified authority. No database or separate cache is required.

## Security, configuration and reliability

### Operating modes and authorisation

`in-process` is the default and has no socket launcher. Only trusted
test/in-process dependencies may inject a typed principal with `research:read`
and `fieldwise-fictional`. Default to deny where absent. Request headers
cannot supply that test identity. This is a process trust boundary.

`loopback` is explicit opt-in. A controlled launcher owns the numeric bind
`127.0.0.1` or `::1` and rejects wildcard, DNS, forwarded and non-loopback
addresses. Validate Host against the corresponding local host and port,
disable proxy headers, permissive CORS and unrestricted docs, and refuse
unsafe mode configuration. Never pass the app factory to an unvalidated
external launcher as an approved configuration. Use a single short-lived
bearer secret injected from the operator environment. Determine valid
syntax before comparing the candidate with the configured secret using
`hmac.compare_digest`. Use exactly one `Authorization` header, a
case-insensitive `Bearer` scheme followed by one ASCII space and one
URL-safe 32–128 character secret (letters, digits, underscore or hyphen).
Missing, expired, malformed, duplicated and mismatched credentials all
give 401 with the same safe message and `WWW-Authenticate: Bearer`.
Valid credentials receive only the fixed research role and audience.
Wrong scope or audience and a disabled capability on a registered
operation give 403. Verify access before checking resource existence.

No client selection, bearer passthrough, permission from arbitrary
`client_id`, raw identifiers, personal data, paths or private files.
Health uses the same bind and host boundary and exposes only fixed
live/ready indicators and safe error envelopes. Public network access,
multi-client routing and live data are deferred. Later shared use needs
separate approval for real identities (for example managed OIDC for
users or mutual TLS for service peers), TLS, storage isolation,
Registry authority, retention and access audit.

### Configuration contract

Use strict parsed settings. Operator environment values are strings by
transport and require explicit parsing into typed values before the factory
validates mode relationships. Refuse unknown `NCI_API_` keys. Unit test
injected settings without modifying real process secrets. Release and
auth settings are supplied by authorised operators.

| Setting | Type and defaults or constraints |
|---|---|
| `NCI_API_MODE` | Literal `in-process` (default) or `loopback`. A label cannot enable another environment. |
| `NCI_API_BUNDLE_ROOT` | Absolute approved read-only directory, required in demo. An unset in-process evidence dependency can use a trusted fixture or stay unready. |
| `NCI_API_RELEASE_SHA256` | `Digest` from trusted external release authority, required for file-backed loading. Root and pin must be configured together. |
| `NCI_API_BIND_HOST` and `NCI_API_BIND_PORT` | Loopback-only address and integer 1024–65535. Defaults `127.0.0.1` and `8000` in loopback. Listener settings are rejected in in-process mode. |
| `NCI_API_BEARER_SECRET` | Secret string with the syntax above, mandatory for loopback and prohibited for in-process. Generate from at least 32 random bytes. Never include a default or serialize the setting. |
| `NCI_API_BEARER_EXPIRES_AT` | Required `UtcInstant` in loopback, future and at most 8 hours from startup, absent in in-process. Validate expiry on each research authentication. Restart with an approved replacement when expired. |
| `NCI_API_LOG_LEVEL` | Literal `INFO` or `WARNING`, defaults to `INFO`. Preserve required access audit events even if diagnostics are filtered. |

Version is fixed by the contract. Transport ceilings are code policy and
cannot be relaxed by environment variables. Cap URL/request target at 2 KiB
and application-visible total request headers at 8 KiB. Reject GET bodies;
read bounded chunks independent of `Content-Length` or reject at ingress.
For ASGI requests that reach the app, enforce 413 on bodies >1 KiB,
400 on a smaller non-empty body, 414 on excessive URLs and 431 on excessive
headers. Malformed HTTP rejected before ASGI can have a server-level
response. Exercise this boundary on the loopback launcher in WP-10.9.

### Errors, logs and performance

Generate a UUID4 request ID for every request that reaches the application.
Return it as `X-Request-ID` and in each `ApiError`. Do not trust incoming
request IDs. Unsupported request shapes receive bounded issue codes with
fixed guidance. Keep a rejection out of the error envelope if it would
disclose evidence identity or input values. Avoid default FastAPI error
serialization of rejected inputs or raw exceptions. Disable exposed stack
traces and sanitise framework access/error logging.

| Status | Stable code | Boundary |
|---|---|---|
| 400 | `INVALID_REQUEST` | Malformed request accepted by transport or unexpected GET body. |
| 401 | `AUTH_REQUIRED` | Missing, invalid, expired or malformed credentials. Use one safe response and Bearer challenge. |
| 403 | `FORBIDDEN` | Insufficient scope/audience or disabled authorised operation. |
| 404 | `NOT_FOUND` | Unknown model after access and readiness checks or unregistered route. |
| 405 | `METHOD_NOT_ALLOWED` | Wrong method on a registered read route. |
| 413 / 414 / 431 | `PAYLOAD_TOO_LARGE` / `URI_TOO_LONG` / `HEADERS_TOO_LARGE` | Request exceeds the corresponding size ceiling. |
| 422 | `VALIDATION_ERROR` | Invalid slug syntax or unsupported query fields. |
| 503 | `SERVICE_UNAVAILABLE` or `EVIDENCE_UNAVAILABLE` | Unready health probe or authorised research request without a valid snapshot. |
| 500 | `INTERNAL_ERROR` | Unexpected internal failure. No exception content. |

Mandatory structured events have UTC time, generated request ID, route
operation ID or constant unmatched marker, status, monotonic duration in
milliseconds, safe category and service version. Add approved opaque
release ID where available and differentiate internal reason codes
`MISSING_EVIDENCE`, `DIGEST_MISMATCH`, `UNSUPPORTED_VERSION`,
`SCHEMA_INVALID` and `POLICY_DENIED` without recording names, paths or
exception strings. Never log bearer contents, raw headers or query strings,
customer data, model inputs, report bodies, private configuration or IP
addresses by default. Scope audit output locally and define retention
before persistent/shared logging.

Liveness remains independent of bundle state. Readiness is all-or-nothing.
Neither performs report verification on request. Run five cold starts
and, after 30 warm-ups, 200 requests per approved route at concurrency
1 and 8 on a documented single-worker reference machine. Report OS, CPU,
RAM, Python and dependency versions, fixture IDs/digests, response bytes,
p50/p95, error rates and peak RSS. Record startup separately. Measure
loopback transport, auth, projection lookups and serialization end to
end, without live evidence. Illustrative budgets pending measurement
are ≤100 ms warm p95 and ≤2 s startup. NFR-002 (<2 s p95 for scoring
excluding upstream retrieval) remains a future operational objective.

### WP-10.9 reference workload

Run from the repository root in the isolated API CI environment:

```bash
PYTHONPATH=src python tests/integration/benchmark_api.py
```

The script generates a temporary, pinned synthetic fixture and uses the
controlled launcher on IPv4 loopback. It measures one worker, five cold
starts to readiness, 30 warm-up GETs per route and 200 measured GETs per
route at both concurrency 1 and 8. This uses 9 routes and
3,600 timed requests.
The client checks response status and records body bytes. Latency includes
local transport, bearer checks where applicable, projection lookups and
serialization. The component probes measure verification and bearer
matching separately in-process. The run did not use retained research
records, frozen models or protected reserves.

The reference host was Linux WSL2 (kernel 6.18.58.1), Intel Core i7-11800H,
16 logical CPUs and 16,244,584 KiB visible memory. Python 3.12.3 used
FastAPI 0.165.0, Starlette 1.10.0, Pydantic 2.14.3, Uvicorn 0.54.0 and
HTTPX2 2.16.2. Fixture bundle size was 8,442 bytes.
Its manifest SHA-256 was `9a4771584de9129cfc58589b788c1797baa727e87ecb02b1fe72a5ffaabcf3d9`.

| Route | C1 p50 / p95 (ms) | C8 p50 / p95 (ms) | Max body (bytes) |
|---|---:|---:|---:|
| `/health/live` | 1.422 / 2.012 | 8.811 / 13.519 | 17 |
| `/health/ready` | 1.504 / 2.238 | 9.714 / 14.900 | 18 |
| `/v1/research/capabilities` | 1.794 / 2.543 | 10.296 / 15.621 | 422 |
| `/v1/research/models` | 1.610 / 2.333 | 8.667 / 12.827 | 2,171 |
| `/v1/research/models/churn` | 1.564 / 1.905 | 9.282 / 13.910 | 1,187 |
| `/v1/research/models/clv/evaluation` | 1.654 / 2.016 | 8.334 / 12.909 | 1,782 |
| `/v1/research/models/churn/limitations` | 1.691 / 2.585 | 9.845 / 13.665 | 2,463 |
| `/v1/research/models/clv/explainability` | 1.755 / 2.197 | 8.970 / 12.999 | 2,270 |
| `/v1/research/segmentation/status` | 1.689 / 2.051 | 8.963 / 26.993 | 856 |

All measured requests returned 200 on the final build. Cold startup
p50/p95 was 571.138/627.003 ms and peak server RSS was
56,052 KiB. Evidence verification p50/p95 was
2.039/6.345 ms and bearer-only p50/p95 was
0.002/0.003 ms. The loopback measurements apply
to this host and representative bounded fixture. They establish neither
a production SLA nor performance for the deferred scoring latency
objective. [Reference benchmark](../../tests/integration/benchmark_api.py).

## Contract verification plan

Future tests use offline pytest fixtures with FastAPI `TestClient` in a
context manager for lifespan, injected monotonic and UTC clocks where
needed, and a test-only trusted bundle root. No real token, external
listener, model binary, existing research workspace or protected reserve is
required in routine CI. Pre-construct a deterministic positive release and
independently supplied test manifest pin. Create each negative fixture by
changing only the relevant variable.

| ID | Area | Deterministic scenarios and expected evidence |
|---|---|---|
| CT-01 | DTOs | Round-trip complete health, model and research payloads. Missing required or null non-null fields fail. Unknown fields, malformed UUID/digests/time, invalid enum and oversize terms fail. Nullable R² requires its reason. Numbers remain finite, monetary strings retain two places, and no unknown metric becomes zero. |
| CT-02 | Routes | Exercise all nine operation IDs and success bodies. Assert empty bodies only, malformed slugs/queries 422, valid unknown model 404 after access, unsupported route 404 and wrong method 405. Assert correct research units, conditions and cache headers. |
| CT-03 | Access | Missing, invalid, expired, double, malformed and valid auth. Verify 401 with challenge, 403 for wrong audience/scope or disabled capability, 404 only for authorised ready unknown model, and no enumeration through differing auth errors. |
| CT-04 | Config and isolation | Reject wildcard/non-loopback bind, unexpected Host/forwarded identities, invalid expiry, absent secret, incomplete evidence settings, unexpected API environment keys, excess headers/URLs/bodies and request-controlled client scope. In-process injected principals are independent of headers. |
| CT-05 | Evidence | Correct independent pin publishes once. Adjacent manifest plus report substitution, changed digest, length drift, missing/mismatched member, invalid UTF-8/JSON/schema, duplicate keys, symlinks, unapproved audience/protocol and model/feature mismatch fail closed. Assert no partial or stale snapshot. Replace files after startup and verify the same approved snapshot is returned until controlled restart. |
| CT-06 | Disclosure | Validate that responses, logs and OpenAPI never contain credentials, raw query/body, account or episode identifiers, reserves, model paths or internal exceptions. Churn/CLV/segmentation/explainability payloads have only approved fields and scales. |
| CT-07 | Lifecycle and OpenAPI | Test startup/shutdown and readiness 503 with healthy liveness 200, one request ID in headers and error body, and safe unknown failure handling. Canonical OpenAPI contains exactly seven secured research operations and two unversioned health operations with closed typed DTOs and error schemas. |
| CT-08 | Bounded reliability | Measure the separate reference workload and startup protocol above. Verify response budgets, safe steady-state behaviour and exact repeatability on fixed fixtures. The WP-10.9 reference table records the results. |

WP-10.2 final verification passed 489 existing package, ingestion,
normalisation, validation, synthetic Registry, Phase 05 feature and pipeline
unit tests, Ruff lint/format and dependency consistency. The isolated
environment passed both the in-process feasibility smoke and a representative
Pydantic nested-variant probe. The latter verified closed `oneOf` generation,
cross-variant rejection, decimal serialization and a required nullable field.
These probes are separate from verification of the eventual nine-route service
against CT-01–CT-08.

## Approved decision register

| Decision | Approved boundary | Implementation control |
|---|---|---|
| API-PO-001 | Internal, synthetic, read-only research scope | No scoring, live clients, commercial prediction or customer intervention. |
| API-PO-002 | Exactly nine GET routes and typed contracts | Explicit DTOs, bounded responses, unversioned health and seven `/v1` operations. |
| API-PO-003 | In-process and authenticated loopback | No public binds, typed in-process authority, short-lived bearer, fixed audience and fail-closed configuration. |
| API-PO-004 | Pinned and verified research evidence | Independent release pin, allowlisted projections, no partial readiness, model loading or reserve exposure. |
| API-PO-005 | Reliability, testing and deployment boundaries | Safe request correlation, offline CI, measured reliability and no later-phase infrastructure. |

The Project Owner approved all five decisions for the Phase 10 research API.
The accepted implementation follows these contracts. A populated evidence
release requires separate approval.

## Implementation increments

### Sequential implementation record

| Work package | Implementation and verification | Gate |
|---|---|---|
| WP-10.4 | Health and capabilities in `api/routes.py`, typed responses in `api/contracts.py`, access checks in `api/security.py`, and the application transport boundary. The default catalogue is absent. A trusted in-process fixture verifies the ready contract, and no retained evidence is served. The 54 API tests and 489 offline regression tests passed with Ruff, targeted mypy and dependency consistency. | Passed |
| WP-10.5 | The model list and detail routes use the immutable catalogue in `api/research.py`. It independently verifies the manifest and all five projected JSON files, validates exact identities and publishes atomically. The 63 API tests and 413 offline regression tests passed. A populated release of retained research has not been authorised or generated. | Passed with isolated fixtures |
| WP-10.6 | Evaluation, limitations, explainability and segmentation status use the typed projections assembled at startup. Isolated tests verify scientific units, required nulls, explanation scales, negative nomination and access precedence. The 68 API tests and 435 offline regression tests passed, with targeted mypy and dependency checks. | Passed with isolated fixtures |
| WP-10.7 | `api/launcher.py` restricts the supported listener to authenticated loopback. `api/audit.py` logs allowlisted JSON events. Tests exercised live request policy through in-process ASGI, with the actual listener mocked in launcher tests. The 71 API tests and 405 regression tests passed. No external deployment was performed. | Passed |
| WP-10.8 | Added canonical OpenAPI contract assertions and the isolated `api-contracts` CI job with the `api-test` extra. The API job install and command passed in a clean local checkout with 74 tests. The safe non-modelling regression passed all 1,092 tests. Hosted verification of the final checkpoint is recorded below. | Passed locally at this increment |
| WP-10.9 | Verified restarted instance isolation and recovery. The 75 API tests and 413 offline regression tests passed. Five cold starts and 3,600 timed loopback requests across nine routes completed on a pinned fixture, with zero non-200 responses. Performance scope and method are recorded in the reference workload above. | Passed for the reference environment |
| WP-10.10 | Reconciled all 20 acceptance criteria, checked strict wire types and safe OpenAPI examples, and reverified the final loopback build. The 77 API tests and 1,092 safe regressions passed. The engineering audit preceded formal Project Owner acceptance and used isolated fixtures. | Passed with documented limitations |

| Package | Responsibility and evidence | Prerequisites / approval |
|---|---|---|
| WP-10.1 | Completed architecture investigation and decision preparation | Gate 01 passed |
| WP-10.2 | Contract design, auth audience, error and release schemas, dependency probe | API-PO-001–005 approved |
| WP-10.3 | Factory, strict settings, dependency resolution and immutable loader boundary | WP-10.2 contract, approved implementation start, synthetic evidence fixture |
| WP-10.4 | Health, version and capabilities with coherent readiness | WP-10.3, transport/diagnostic protections. Activate research auth and redaction with capabilities before its first exposure |
| WP-10.5 | Verified model cards and provenance projections | WP-10.3/10.4, enforced auth and separately authorised evidence descriptors for real release readiness |
| WP-10.6 | Bounded evaluation, explanation and segmentation projections | WP-10.5 and approved report field allowlists |
| WP-10.7 | Enforce auth, error redaction, input limits and safe audit wiring | WP-10.2/10.3. Land authorisation, fail-closed config, request limits and safe errors together with the first research route. WP-10.7 hardens and verifies controls |
| WP-10.8 | Unit, integration, negative auth and OpenAPI tests; enable API CI | WP-10.3–10.7, tests developed with increments |
| WP-10.9 | Reliability and reference workload verification | WP-10.8, owner-approved environment and budget |
| WP-10.10 | Runbook, evidence matrix and engineering recommendation | Engineering gates verified. Formal acceptance is recorded below. |

## Acceptance matrix

These statuses apply to the accepted Internal Research & Analytics API.
The requirements reconciliation retains the original functional and
non-functional requirements outside that scope.

| ID | Requirement | Verification and expected evidence | Acceptance condition | Dependencies | Status |
|---|---|---|---|---|---|
| API-01 | Approved business scope | Review owner-approved scope and capability catalogue | Research-only exposure and exclusions approved | PO-001, WP-10.2 | Passed |
| API-02 | Architecture | Review component dependency and startup design | Owner agrees local modular service boundary | PO-002/003/004, WP-10.2 | Passed |
| API-03 | Versioning | OpenAPI and compatibility tests | Prefix and independent version fields stable | WP-10.4/10.8 | Passed |
| API-04 | Request contracts | Positive and negative request tests | Strict bounded inputs, unsupported fields rejected | WP-10.3/10.7/10.8 | Passed |
| API-05 | Response contracts | Schema and payload budget tests | Only closed, valid DTOs returned | WP-10.5/10.6/10.8 | Passed |
| API-06 | Safe errors | Exercise transport, validation, evidence and internal failures | Stable codes and no sensitive exception content | WP-10.7/10.8 | Passed |
| API-07 | Model provenance | Compare released cards to pinned fixtures | Identity, experiment, target and version match | PO-004, WP-10.5/10.8 | Passed with documented limitations |
| API-08 | Evidence integrity | Tamper, absence and incompatible bundle fixtures | Closed readiness, no substituted evidence | WP-10.3/10.6/10.8 | Passed with documented limitations |
| API-09 | Churn restrictions | Route absence and card assertions | Scope and weak metrics visible; no scoring or bands | WP-10.5/10.8 | Passed |
| API-10 | CLV semantics | Contract tests for target, grain, horizon and units | Gross issued GBP and clipping accurately described | WP-10.5/10.6/10.8 | Passed |
| API-11 | Segmentation restrictions | Assert non-nomination and denied assignments | Research status only | WP-10.6/10.8 | Passed |
| API-12 | XAI governance | Assert method, scale and safe projection | Distinct scales, no identities, local cases or causal claims | WP-10.6/10.8 | Passed |
| API-13 | Security | Access, binding, host and limits tests | Fail closed under unsafe config and unauthorised requests | PO-003, WP-10.7/10.8 | Passed |
| API-14 | Client isolation | Wrong audience and client override tests | Fixed audited scope and no cross-client reads | PO-003/004, WP-10.7/10.8 | Passed |
| API-15 | Configuration | Strict validation, missing secret and unsafe path fixtures | Invalid settings fail startup without secret disclosure | WP-10.3/10.8 | Passed |
| API-16 | Health and readiness | Lifespan tests with verified and unavailable evidence | Live remains observable and readiness gates every research request | WP-10.4/10.8 | Passed |
| API-17 | Observability | Inspect structured logs under success and failure | Correlated, bounded and redacted evidence | PO-005, WP-10.7/10.8 | Passed |
| API-18 | Automated verification | Local offline checks, hosted GitHub Actions for the accepted checkpoint and reference workload results | API tests, safe regressions and agreed reliability checks pass | WP-10.8/10.9 | Passed |
| API-19 | OpenAPI and documentation | Contract snapshot and operator walkthrough | Versioned documentation matches protected implementation | WP-10.8/10.10 | Passed |
| API-20 | Reproducibility and boundaries | Repeat startup on fixtures and audit Git/artefacts | Same verified projection, no model execution or later-phase changes | WP-10.9/10.10 | Passed |

### Final engineering review and operator boundary

The implemented Python modular monolith exposes only the nine approved GET
routes. The health surface is independent of evidence for liveness and
checks the atomically published snapshot for readiness. All research
responses require the fixed fictional audience and research authority.
The API reads pinned, closed projected JSON at startup and derives typed
responses in memory. No request opens a source report or model binary.
The architecture preserves the approved Python, FastAPI and Power BI split.

The local engineering verification passed 77 isolated API tests and
1,092 safe existing regression tests. The regression exclusions are recorded
in the CI workflow. Historical model-fitting, scoring and research notebook
collections were excluded from this verification. Ruff, targeted mypy
and dependency consistency passed.
The final audit removed unintended type coercion for approval flags and
integer fields. An initial repeat of the startup workload exposed a strict
UTC conversion error. The parser now converts the validated timestamp
explicitly, the published timestamp has a regression assertion, and the
full reference workload passed on the corrected build.

API-07 and API-08 are limited to fixture-backed verification. A populated
release of retained summaries and its independently supplied pin require
explicit Project Owner approval. The secure bundle reader requires POSIX
directory-relative descriptor and no-follow support and fails closed where
unavailable. The reference workload remains a single-host measurement.

Use the default in-process factory for offline application verification.
For an authorised demonstration with an approved release, supply the
settings in this document from the operating environment, then use
`python -m nowa_customer_intelligence.api.launcher`. The approved launcher
refuses non-loopback settings, disables proxy headers and emits redacted
audit records. Keep the secret and pin outside the bundle and outside source
control. Rotate the bearer secret at expiry. Update the release and its
independent pin through the approved release process, then restart for
atomic verification. A valid configuration with unreadable evidence keeps
liveness available and readiness at 503. No public deployment, multi-tenant
access, operational inference or dashboard implementation was introduced.

## Project Owner acceptance

**PHASE 10 — API DEVELOPMENT: ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS.**

The Project Owner formally accepted checkpoint
`8403b4fc44000f2744350d03a09c1052b4391c7e` for the Internal Research &
Analytics API. Acceptance covers the modular FastAPI architecture, nine GET
endpoints, Pydantic and OpenAPI contracts, authentication and authorisation,
verified evidence architecture, safe errors and structured audit logging.
The approved access boundary is read-only synthetic research through
in-process or authenticated loopback access. Production or commercial deployment,
operational model scoring, customer-specific predictions, retained-evidence
publication and multi-tenant access remain outside this approval.

### Hosted GitHub Actions verification

The `CI` workflow completed successfully on 22 November 2026 after the
push of the accepted checkpoint to `main`. Both jobs used CPython 3.12.16
and installed their declared dependencies successfully.
[GitHub Actions run 45032629816](https://github.com/AnderCruz/Customer-Churn-Prediction-CLV/actions/runs/45032629816).

| Job | Job ID | Verified result |
|---|---|---|
| `api-contracts` | `137239343696` | 77 API tests passed with zero failures or skips. Dependency consistency passed. |
| `quality-and-tests` | `137239344022` | 1,092 safe regression tests passed with zero failures or skips. Ruff lint and formatting passed. |

The safe regression job excluded the API tests, which ran separately, and
the nine research collections specified in the CI workflow. This run
satisfies the hosted verification requirement for API-18. API-07 and API-08
remain accepted with the documented release and filesystem limitations.

**PHASE 11 — DASHBOARD DEVELOPMENT: PENDING.** Formal initiation requires
separate Project Owner authorisation.
