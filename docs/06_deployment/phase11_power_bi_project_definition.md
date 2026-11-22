# Phase 11 Power BI project definition and business requirements

**Document ID** · NCI-DASH-001\
**Version** · 0.1\
**Status** · Accepted as the Project Definition and Business Requirements baseline\
**Work package** · WP-11.1, Project Definition & Business Requirements

## 1. Authority and baseline

**PHASE 11 — POWER BI DASHBOARD DEVELOPMENT: IN PROGRESS.**

The accepted Phase 10 checkpoint `922528a90270c5df79e56868163d66839bd48d29`
matched local `main`, `origin/main` and live GitHub `main` at the
start of the WP-11.1 review. The index and working tree were clean. DASH-PO-001–004
approve Microsoft Power BI as the primary dashboard platform, Python for
analytics and dataset preparation, a verified dataset boundary and a
synthetic research scope. Power Query and DAX perform preparation within
Power BI and define analytical measures. FastAPI remains the application
services layer. The initial report must refresh and render with FastAPI
stopped. Historical Streamlit references are superseded for Phase 11.
[Roadmap and dashboard decisions](../07_project_management/implementation_plan_and_roadmap.md#24-phase-11-dashboard-development),
[Phase 10 acceptance](phase10_api_architecture_and_contracts.md#project-owner-acceptance).

The review applied NEDS v1.1, including phase governance, data management,
explainability, testing, security, version control and British English.
The repository records the approved 14-phase sequence. A separate signed
roadmap and standalone Project Charter were unavailable for independent
review. This proposal uses the repository alignment and the owner brief.
Existing product requirements and their priorities remain in force.
[Phase alignment](../07_project_management/implementation_plan_and_roadmap.md#2-phase-alignment),
[business objectives](../01_business/business_objectives_and_scope.md),
[Phase 01 setup](../PHASE_1_SETUP.md),
[Phase 02 data quality](../04_data/data_quality_specification.md),
[Customer Data Contract v1.1](../04_data/customer_data_contract.md),
[architecture decisions](../03_architecture/architecture_decisions.md),
[canonical identity](../03_architecture/adr_episode_identity_and_identifier_management.md),
[MVP technical design](../03_architecture/mvp_architecture_and_technical_design.md).

### Project Owner decisions

BI-PO-001–007 supplement the existing DASH-PO-001–004 architecture decisions.
The Project Owner formally initiated Phase 11, accepted WP-11.1 with the
boundaries below and authorised WP-11.2 specification work.

| Decision | Approved scope |
|---|---|
| BI-PO-001 — Phase 11 initiation | Accept WP-11.1 as the planning baseline and authorise WP-11.2 specification work. |
| BI-PO-002 — Dashboard scope | Retain the six pages in §3. Gate each page on approved data availability, applicable disclosure approval and successful page acceptance checks. Show unavailable evidence as unavailable. |
| BI-PO-003 — Initial data source | Use authorised Fieldwise Cloud synthetic inputs and accepted research evidence. Defer Misata, UCI and other external sources. |
| BI-PO-004 — Research aggregate disclosure | Review each research aggregate field before release. Preserve the separate Phase 10 evidence release boundary. Operational scoring, customer-specific predictions and protected reserves are outside scope. |
| BI-PO-005 — Development environment | Prepare inputs in Python on Linux and author in Power BI Desktop on Windows. Prefer PBIP after a save, reopen and refresh proof. PBIX is an approved local fallback. |
| BI-PO-006 — Distribution scope | Restrict initial development and review to local research. Service publication, public sharing, live client data and production infrastructure remain outside scope. |
| BI-PO-007 — Mandatory quality gates | Require contract approval, dataset quality and integrity, financial reconciliation, validated model relationships, DAX reconciliation, research disclosure approval, report validation, security and reproducibility. Approve contracts before dataset implementation and validate relationships before final DAX. Reconcile DAX against independent Python values. Perform final visual and refresh verification on supported Windows. A failed gate blocks dependent work. |

See the [WP-11.2 analytical data contracts](phase11_analytical_data_architecture_and_contracts.md).
The [BI-DR-001–010 register](phase11_analytical_data_architecture_and_contracts.md#12-project-owner-decision-register)
records the later owner dispositions. WP-11.2 remains pending formal
acceptance and WP-11.3 remains pending.

## 2. Business purpose and users

Provide one local Power BI report with up to six pages for internal review
and controlled synthetic demonstrations. The descriptive pages answer
what the fictional population did, over what period and with what coverage.
The research pages show what accepted experiments measured and the limits
on interpretation. Scientific claims and operational decisions remain
governed by the accepted phase records.

| Persona | Decision or review need | Proposed outcome |
|---|---|---|
| Executive or Project Owner | Check population, historical billing and which analytical capabilities have supporting evidence. | Understand headline metrics, coverage and research approval at a glance. |
| Revenue Operations or finance analyst | Explain issued billed value, billing cadence and the difference between invoice issuance and monthly-normalised contractual amounts. | Reconcile historical totals and understand the scope and error of the six-month billed-value forecast. |
| Customer Success analyst | Inspect historical account, episode and usage patterns. | Review descriptive cohorts and RFM evidence without customer targeting or operational assignments. |
| Data scientist or engineering reviewer | Check an evaluation or explanation against the accepted experiment. | Identify the model, partition, target, scale, support, date, source version and scientific restrictions. |
| Report author or data steward | Refresh locally and verify that the input and report definitions match the approved version. | Reproduce figures and trace differences to a specific bundle, contract or measure. |

Historical metrics use Fieldwise Cloud synthetic observations. They provide
no estimates of market prevalence, future client performance or financial
returns. The proposal excludes live client data, per-customer scoring or
explanations, risk bands, revenue-at-risk calculations, operational segment
assignments, model fitting, reserve access and public distribution.

## 3. Proposed page catalogue

Every page needs a visible synthetic-data label, data or evidence version,
date range or cut-off, and a description of its grain. Research visuals also
show the experiment, evaluation partition, support and intended use. A page
whose required extract is missing remains unavailable with a reason.

| Page | Purpose and audience | Indicators and permitted visuals | Required evidence and feasibility | Acceptance and restrictions |
|---|---|---|---|---|
| 01 — Executive Overview | Executive and owner review of historical scale, coverage and research status. | Distinct accounts, observed episodes, gross issued GBP, invoice count, coverage dates and available research capabilities. Use KPI cards, a monthly line chart and a status table. | Historical facts and version manifest from a new Fieldwise projection. Accepted reference totals are available for reconciliation. Capability statuses can use accepted governance records. | Totals match the approved reference at the unfiltered scope. Each KPI defines its date and denominator. Capability status shows experimental and limited approvals without implying commercial readiness. |
| 02 — Customer Analytics | Customer Success and Revenue Operations review of historical cohorts, cadence and billing or usage patterns. | Accounts, episode counts, monthly and annual billed amounts, recurrence and usage coverage. Use cohort matrices, cadence bars, aggregate distributions and monthly trends. | New Fieldwise account, episode, snapshot, invoice and usage projections. Phase 05 bundle is supporting evidence for point-in-time and missingness definitions. | A successor episode stays distinct from its predecessor. Date and cadence filters reconcile to approved totals. Usage percentages expose eligible and observed denominators. Historical reporting omits customer identifiers and account drill-through. |
| 03 — Churn Research | Technical review of the frozen 30-day contractual churn classifier for a subscription episode. | Development-validation AP against the dummy baseline, ROC-AUC, precision, recall, confusion counts and validation support. An accepted aggregate error or threshold diagnostic may be shown. Use model comparison bars, diagnostic charts and a limitations panel. | Saved Phase 06 results verified locally. Requires an allowlisted aggregate evaluation extract. | Show 717 validation rows and eight positive accounts, weak ranking, 695 false alerts at the fixed threshold and the missed confirmation floor. Label the holdout unscored. Leave out score lists, risk bands, targeting and claims of calibration or commercial validity. |
| 04 — CLV Analytics | Finance and technical review of research forecasting future gross issuance. | Frozen-model MAE versus the validation baseline, bias, error by supported cadence and horizon maturity. Use metric cards, aggregate error bands and a definition panel. | Phase 07 accepted record and retained report present. Requires a development-validation-only aggregate extract. | Identify `future_6m_issued_gbp` at canonical account and UTC month-end observation grain. The interval is open at observation and closed at six calendar months, in gross issued GBP. Show row and account support and caveats about clipping and cadence. Cash collection, recognition, profit, margin, discounting and lifetime extrapolation are outside the measure. |
| 05 — RFM & Segmentation | Review historical financial profiles, cadence differences and model nomination. | RFM distributions, eligibility and short-history counts, cadence support, method agreement and candidate disposition. Use aggregate bars, distributions and an eligibility table. | Phase 08 report and deterministic boundary artefacts present. Requires a development-only aggregate projection of the approved methods. | Label account grain, UTC cut-off and 12-calendar-month window. Show **no operational model nominated**. Preserve unsupported cadence and incomplete usage status. Hide membership, customer assignments and unstable or unsupported groups. |
| 06 — Explainable AI | Technical and governance review of what the frozen models relied on. | Mean absolute attribution, support, background and approved stability summaries. Use separate bar charts or tables by method and scale. | Four Phase 09 report fingerprints matched. Requires separately reviewed aggregate field selections. | Label churn TreeSHAP class-1 probability and log odds separately. Show the CLV four-block method on the final clipped GBP predictor. Report associations, background sensitivity and uncertainty. Omit local cases, cross-scale ranks and causal interpretations. |

The churn evidence has low positive support and inadequate operational
ranking. CLV validation contained 355 observations from 180 accounts,
with aggregate MAE £58.27 against a £112.96 training-median baseline on that
partition. Cadence differences, bias and repeated observations limit
interpretation. Phase 08 approved deterministic financial profiles with
point-in-time eligibility. Every clustering candidate failed a nomination
gate. Phase 09 attributes model output and preserves separate methods,
reference distributions and units. Reported metrics remain research
evidence, with no fresh prediction or evaluation in Phase 11.
[Churn acceptance](../07_project_management/implementation_plan_and_roadmap.md#191-project-owner-final-acceptance),
[CLV definition and evaluation](../05_ml/phase07_clv_economic_definition_and_validation.md),
[Segmentation scope](../05_ml/phase08_segmentation_scope_and_validation.md),
[Explainability evidence](../05_ml/phase09_explainability_scope_and_validation.md).

## 4. Data availability and analytical dataset requirements

| Source | Availability verified for WP-11.1 | Proposed use and boundary |
|---|---|---|
| Fieldwise Cloud seed 42, Phases 03–04 | Accepted 1 April 2021 to 31 March 2024 reference and reproducible Python pathway. No five-file reference export is present under `data/raw`. The accepted records describe temporary exports and explicitly bounded reproducibility. | Proposed primary descriptive source. After approval, run the existing reference workflow on authorised development inputs, with its acceptance and integrity checks, into a new ignored location. Preserve the source Registry authority and report the identifier scope and any replay differences. |
| Phase 05 point-in-time feature bundle | Manifest, observations, predictors and prediction-eligibility artefacts matched prior SHA-256 fingerprints. | Use accepted aggregate availability, eligibility and missingness definitions where useful. Predictor rows, identities and outcomes are outside the reporting dataset. |
| Phase 06 development evidence | Baseline, advanced report and manifest matched prior SHA-256 fingerprints. | Select only approved aggregate development-validation measures. Keep the unscored reserve and the historical Batch 09 period out of the dashboard workload. |
| Phase 07 and Phase 08 research | Phase 07 report and manifest and Phase 08 report, protocol, design, manifest and RFM boundaries were present. This review used accepted summaries for facts and left those retained file contents unopened. | Require a reviewed aggregate-only projection and integrity verification at the data-contract gate. Select development-validation CLV evidence and approved descriptive RFM evidence. Use no reserve data or new research outputs. |
| Phase 09 explanation evidence | Protocol, compatibility, churn and CLV report digests matched the retained manifest. | Use approved development summaries if the selected fields pass provenance and disclosure review. Leave case-level records and compatibility-only raw outputs out of the report. |
| Misata and UCI Online Retail II | Both local archive and provenance pairs matched prior SHA-256 fingerprints. Phase 03 approved independent local analysis and Phase 04 used the sources separately. | Exclude from the initial report proposal. Misata is third-party fictional with native USD amounts. UCI is historical retail invoice-line evidence with different grain and permitted uses. Any expansion requires separate scope and source-use review. |
| Dashboard-ready bundle, released API evidence, live client or reserve data | No dashboard-ready bundle was verified. Phase 10 retained-evidence release remains subject to API-07. Live client and reserve data are outside the authorised scope. | Build only the approved synthetic and aggregate projections in a later increment. Keep the API release, protected reserves and live data outside the refresh path. |

The accepted Fieldwise reference has 1,000 accounts, 1,200 episodes,
14,787 invoices, 16,547 monthly usage rows and 18,661 snapshots.
Gross issued amount was £1,566,111.80. These are baseline reconciliation
controls for their documented scope, with any dashboard-specific
population filter reconciled separately. Report refresh date, source
extraction cut-off and observation or invoice date are distinct.
[Acquisition and EDA records](../07_project_management/implementation_plan_and_roadmap.md#16-phase-03-final-technical-review),
[Phase 05 feature contract](../07_project_management/implementation_plan_and_roadmap.md#18-phase-05-point-in-time-feature-engineering),
[source governance](../04_data/data_sources_and_governance.md#8-approved-complementary-phase-03-sources),
[Fieldwise reference interface](../../src/nowa_customer_intelligence/data/eda_inputs.py).

### Proposed delivery inventory

These are logical datasets. WP-11.2 would settle file schemas, mandatory
fields, keys, coverage, validation tolerances and the release process.
Each projected delivery must be traceable to the accepted source or
experiment and contain an explicit contract version and batch identity.

| Dataset | Business purpose and originating source | Proposed grain, key and coverage | Types, units and quality requirements |
|---|---|---|---|
| Historical dimensions | Account and episode grouping from Fieldwise customer and subscription exports. | One record per account or episode within the verified bundle. Use separate bundle-scoped keys and an episode-to-account reference. Calendar covers certified history and its applicable date roles. | Opaque text keys, dates and approved categories. Enforce unique keys, valid foreign keys and coherent predecessor and successor boundaries. Keep original identifiers outside Power BI. |
| Historical billing | Invoice counts, cadence and gross issue trends from verified Fieldwise invoices. | One included invoice per hidden bundle-scoped invoice key at issue date, with episode or approved reporting keys. Source coverage April 2021–March 2024. | ISO dates, integer counts, ISO currency and exact GBP values. Reconcile issue amounts and counts to source, verify unique invoice attribution and retain cadence context. Future adjustment treatments require review. |
| Historical subscription state | Review episode status and monthly-normalised contractual amounts from Fieldwise snapshots. | One episode per observation date. Separate canonical episodes and mark coverage and latest valid snapshot selection explicitly. | Dates and UTC timestamps where applicable, status categories, nullable fixed-decimal GBP per month. Point-in-time eligibility and time roll-up require validation. |
| Historical usage and coverage | Describe usage within supported periods from Fieldwise monthly usage and approved availability evidence. | One episode per labelled month with eligible and observed coverage. The accepted EDA records completed observed months through February 2024. | Integer user, session and event counts, period bounds and coverage status. Distinguish actual zero, missing, structural absence and evidence awaiting reporting. Avoid sums of active users across episodes as a distinct-account count. |
| Evaluation metrics | Reproduce approved Churn and CLV results from retained Phase 06–07 summaries. | One experiment, model, named development-validation partition, metric and approved cohort. Churn validation begins 1 April 2023 and is strictly before 1 September 2023 with the accepted maturity rule. CLV validation uses January and February 2023 month ends. | Text IDs, decimal metric, named statistics and units, row and account counts. Explicit support, baseline comparability, denominator and cut-off. Preserve unknown metrics and reject any unapproved partition. |
| RFM and segmentation summary | Describe approved Phase 08 financial profile distributions, coverage and nomination. | One approved development observation cut-off, methodology and band, cadence or coverage category. March and December 2023 and March 2024 cut-offs have different roles. | Whole-account counts, recency in days, frequency in invoices, monetary in gross issued GBP. Reconcile classifications and suppress unsupported combinations. Do not transfer scores or cluster identifiers as assignments. |
| Explainability summary | Review Phase 09 frozen attribution and stability evidence on approved development samples. | One model, method, scale, reference set, feature or block, and named statistic for the accepted validation sample. | Explicit probability contribution, log odds or clipped GBP units, sample and independent account counts where recorded. Use fitted feature lineage labels and separate scales and background variants. |
| Evidence manifest and KPI dictionary | Trace each dataset and measure to accepted inputs and show coverage and freshness. | One row per approved bundle component and contract version, with source or experiment keys and measurement-definition references. | Source Git SHA, file digest, row count, date bounds, schema and producer versions, approved scope, data type and unit metadata. Verify hashes and exact inventory before refresh. |

All analytical datasets would be newly prepared projections of existing
accepted evidence. For each, record the source and transformation
versions, exact approved input hashes, output schema and hash, coverage
limits, omission reasons and usage restrictions. Refresh historical data
manually from one approved immutable batch. Refresh experimental
summaries only when separately authorised. Restrict initial local access
to the Project Owner acting as Data Steward. Transfer only the permitted
projection and manifest. Do not expose sensitive fields through hidden
columns or use full research reports as Power Query sources.

## 5. Technical architecture and semantic modelling

**Python on Linux → verified versioned analytical bundle → Power Query in
Power BI Desktop on Windows → semantic model and DAX → native report visuals.**

1. Python owns canonical identity, temporal eligibility, financial rules,
   evidence projection, validation and manifest generation. Evaluate typed
   UTF-8 CSV plus a JSON manifest as the low-complexity handoff. WP-11.2
   would confirm type and precision fidelity, local path portability and
   whether a typed alternative is warranted.
2. Power Query imports the verified bundle from a local parameterised root.
   Set explicit locale, data types and date interpretation. Report schema
   or refresh failures visibly. Keep scientific and financial rules in their
   authoritative Python implementation. Import mode fits a fixed review
   dataset and keeps the workflow independent of live services.
3. Use separate billing, episode-snapshot and usage facts with validated
   dimensions. Keep research facts separate from historical facts. Scope
   experimental filters to compatible experiment, method, partition and
   scale. Prefer one-to-many, single-direction filters. Disable ambiguous
   paths and test cardinality and orphan keys. Use explicit issue,
   observation and usage-period date roles. [Microsoft star-schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema).
4. Use explicit DAX measures and recognised blank values. Gross issuance
   is additive over disjoint qualifying invoices in GBP. Snapshot monthly
   contractual amounts represent a selected date and cannot sum over
   repeated snapshots. Distinct accounts and episodes require their own
   keys and filter context. Never average AP, MAE, precision or attribution
   values across partitions or scales. Render approved precomputed values
   with their support and suppress undefined percentages.
5. Use native visuals and an approved local Windows Power BI Desktop build
   for opening, refresh and visual review. The inspected shell runs Linux
   and exposes the Windows PowerShell executable on its path. A usable Power
   BI Desktop build and compatible authoring settings remain to be demonstrated. Pin the
   verified Desktop build for reviewers and use a local checkout or approved
   local transfer with identical digests. Keep Python validation in Linux.
   [Power BI Desktop requirements](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop).

Prefer **Power BI Project (PBIP)** if the selected Windows Desktop build
can save, reopen and refresh the project from a clean checkout. A PBIP
stores report and semantic-model definitions in reviewable text files. Git
would track the project pointer, report and semantic model definitions,
approved query and measure definitions and documentation. Exclude
`.pbi/cache.abf`, `.pbi/localSettings.json`, datasets, local paths and
credentials. Inspect project diffs for embedded data and reject unexpected
cache or output files. Evaluate PBIX as an owner-approved local fallback
if compatibility fails. It is a binary review artefact with limited Git
diff visibility and can contain imported data, so keep the review copy
outside Git and keep source contracts, measures and run instructions
reviewable. No PBIP or PBIX artefact was created during WP-11.1.
[Power BI Desktop projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview).

## 6. Functional and non-functional requirements

| Proposed requirement | Verification and product traceability |
|---|---|
| DASH-FR-01 — Show historical account, episode, invoice and coverage KPIs with source, date, grain and definition. | Reconcile against accepted Fieldwise totals and a filtered control. Supports FR-035 and the historically supportable portion of FR-021. |
| DASH-FR-02 — Offer descriptive date, cadence and cohort filters and a consistent reset. | Check expected cross-filter effects and totals. This descriptive filtering leaves the original risk or segment filter requirement FR-040 outstanding. |
| DASH-FR-03 — Show accepted research methods, evaluation, support and limitations with gated availability. | Compare directly with approved aggregate evidence. Supports FR-039, FR-024 and the aggregate research portions of FR-022–025 and FR-032–034. |
| DASH-FR-04 — Include historical RFM coverage and negative operational nomination. | Compare definitions and cut-off counts with accepted Phase 08 evidence. FR-026–028 operational deliverables remain outstanding. |
| DASH-FR-05 — Verify the input bundle before local refresh and show dataset version, coverage and provenance. | Test expected and mismatched inputs. Supports FR-007, FR-042 metadata and FR-045 identifier minimisation. |
| DASH-FR-06 — Exclude operations and data outside the approved report scope. | Inspect projections, report navigation, drill-through and export paths. FR-015–020 scoring, FR-029–031 and FR-038 revenue at risk, FR-036 risk views, operational aspects of FR-037, local customer explanations under FR-033 and scored export under FR-041 remain unresolved product obligations. |
| DASH-NFR-01 — Reproducible, local and reviewable refresh. | On an approved Windows/Desktop build, reopen a clean checkout with a hash-verified bundle and reproduce reference values. Python contract tests remain offline. Trace to NFR-005, NFR-021–024 and AC-015/017. |
| DASH-NFR-02 — Measure standard page load and filter response. | Establish reference Windows build, hardware, bundle and scope. Record initial and repeated loads for agreed pages. Assess the existing NFR-003 five-second page-load target, record interaction and refresh timings separately and retain Performance Analyzer traces. No performance claim has been measured in WP-11.1. [Performance Analyzer](https://learn.microsoft.com/en-us/power-bi/desktop-performance-analyzer). |
| DASH-NFR-03 — Provide accessible, interpretable content. | Review keyboard navigation, focus order, alt text, contrast, titles, visible units, denominators and a table or text where colour carries a distinction. Trace to NFR-033/035/036. [Power BI accessibility](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-accessibility-creating-reports). |
| DASH-NFR-04 — Apply least privilege, minimisation, bounded refresh failures and controlled retention. | Validate local file permissions, deny unauthorised data, inspect cache and exports, test clear failure reporting and record refresh metadata without input rows or secrets. Trace to NFR-011–017/019 and AC-018. |

AC-013 supplies the dashboard demonstration expectation. The proposed pages
can demonstrate the approved subset with reference data, while the original
operational requirements retain their status. AC-007/008/011/014 and
operational interpretations of AC-009/010/012 need their own evidence and
approval. Deployed role access under FR-044 and packaging under AC-016
remain separate. [Functional requirements](../02_requirements/functional_requirements.md),
[Non-functional requirements](../02_requirements/non_functional_requirements.md),
[Product acceptance criteria](../02_requirements/acceptance_criteria.md).

## 7. Security, refresh and distribution

- Restrict initial access to the Project Owner acting as Data Steward
  under BI-DR-005.
  Use controlled filesystem access and approved local storage. Prevent
  dataset or cached report copies from entering Git or unauthorised cloud
  sync. Treat PBIX, caches and exports as data-bearing artefacts.
- Refresh from one explicitly selected, checksum-verified bundle. Record
  operator, time, source version and outcome. On invalid data keep the
  previous verified report labelled with its version and refresh failure,
  or block the view when a trustworthy previous version is unavailable.
  Retain the verified bundle and one rollback version until replacement
  approval. Any later authorised reviewer-copy workflow must enforce
  the proposed 30-day maximum. Reviewer copies are outside current scope.
- Permit only approved aggregate views and exports, subject to a disclosure
  review covering small cohorts, filtered differences, drill paths and
  underlying data. Choose an explicit small-group policy before release.
  A hidden column or a report-level option is insufficient protection for
  a model file in a user's possession. Exclude restricted fields upstream.
- Public sharing, Publish to web, service workspaces, scheduled refresh,
  gateways and commercial distribution require separate owner approval.
  Future sharing needs named audiences, tenant and workspace controls,
  export restrictions, retention and an access audit. Confirm the then-current
  licence and capacity for both authors and consumers before any commitment.
  [Power BI service licensing](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-features-license-type).
- Keep API-07 retained-evidence publication separate. A dashboard extract
  requires approval of the dashboard field list and audience. It grants
  no permission to publish a retained Phase 10 API release or use its
  restricted source reports. API-08 and the accepted API scope remain in force.

## 8. Proposed engineering plan and quality gates

BI-PO-007 establishes the required gate order. The detailed test scope and
evidence for later increments remain subject to review. Each increment
records its actual verification results.

| Work package | Dependency and proposed deliverable | Quality gate |
|---|---|---|
| WP-11.1 — Project Definition & Business Requirements | Accepted Phase 10 baseline and existing DASH-PO-001–004. | Planning baseline accepted and Phase 11 initiated under BI-PO-001–007. |
| WP-11.2 — Analytical Data Architecture & Contracts | Specification authorised. Define source inventory, projections, data dictionary, schemas, KPI semantics, disclosure and refresh rules. | Approve provenance, grain, key and type rules, reconciliation targets and failure cases before dataset implementation. Release of research fields and cohorts requires a separate disclosure approval. |
| WP-11.3 — Power BI Semantic Model | Pending separate authorisation under BI-DR-008. The BI-DR-007 Windows fixture proof is a separate approval. | Clean checkout opens in the pinned toolchain. Relationship and date tests establish defined filter behaviour. |
| WP-11.4 — Power Query & Data Transformation | Approved contracts and model design. Implement Python projections and Power Query imports, then complete the physical model. | Valid bundle refreshes deterministically. Missing, altered or incompatible inputs fail safely. No restricted data enters the delivery. |
| WP-11.5 — DAX Measures & Financial KPIs | Verified first refresh and validated semantic model. Define and test explicit measures and filter behaviour. | Independent Python totals agree with report measures over the reference and selected filters, including blank, zero, currency, date and identity cases. |
| WP-11.6 — Executive & Customer Dashboards | Approved historical measures and bundle. Build pages 01–02. | Owner or delegate reconciles headline and filtered values, coverage and business labels. |
| WP-11.7 — Churn, CLV & RFM Dashboards | Approved research projections and shared report controls. Build pages 03–05 where evidence is ready. | Report values match accepted development evidence. Restricted functions, false claims and unsupported groups are absent. |
| WP-11.8 — Explainable AI & Model Performance | Approved summary fields and evaluation conventions from WP-11.7. Build page 06 and consolidate provenance and performance context. | Verify method, scale, support, frozen identity, sampling context and research-only interpretation. |
| WP-11.9 — Testing, Security & Performance | Approved report pages and reference environment. Execute cross-page checks and Windows review. | Pass offline data tests, Windows refresh and filter checks, accessibility, export review and measured performance against the agreed target. |
| WP-11.10 — Documentation & Engineering Acceptance | Complete and independently review gates. Produce setup, refresh, measure dictionary, evidence and limitations record. | Reproduce the delivery from a clean checkout. Record any qualified results and obtain formal owner acceptance separately. |

This keeps the suggested order. WP-11.3 establishes logical relationships and
toolchain feasibility first. WP-11.4 completes the physical model after
verified data import, so empty report structures cannot be mistaken for a
validated model. Each research page depends on its own aggregate approval.
The descriptive pages can be reviewed independently if a research extract
is blocked. Any page deferral requires the owner to agree the revised scope.

## 9. Proposed delivery acceptance

| Gate | Required evidence |
|---|---|
| DASH-AC-01 — Scope and provenance | Approved source and aggregate field register. Match every imported table to an immutable manifest and accepted source or experiment. |
| DASH-AC-02 — Financial and temporal correctness | Reference control totals reconcile. Date-role, cadence, reactivation, duplicate, zero and missing-value tests pass without cross-grain aggregation. |
| DASH-AC-03 — Page demonstration | Each approved page renders the indicators in §3, with visible data limitations and a verified filter and reset path. Owner records any agreed page deferral. |
| DASH-AC-04 — Research claims | Verify model and report versions, development cohort support, CLV economic units, negative nomination and XAI output scales. Reserve, scoring and causal claims stay outside the report. |
| DASH-AC-05 — Security and distribution | Approved local audience, files, permissions and export policy. Verify the import model and Git inventory contain only permitted values, definitions and documents. |
| DASH-AC-06 — Reproducibility and reliability | From a clean checkout on the approved Windows build, open, refresh, reproduce the reference values and show useful errors on invalid inputs. Record NFR-003 measurements and accessibility results. |
| DASH-AC-07 — Phase closure | Record verification evidence, known limitations, data dictionary and operator instructions. Obtain separate owner acceptance and preserve the later phase boundaries. |

## 10. Dependencies, risks and owner decisions

| Dependency or risk | Effect and proposed control |
|---|---|
| Windows build and PBIP compatibility unverified | Blocks authoring acceptance until a named Windows/Desktop build passes a save, reopen and refresh proof. Choose a controlled fallback if needed. |
| Dashboard extracts and field approvals outstanding | Blocks report refresh and research page release. Approve bundle contracts and aggregate allowlists before import. A missing input must never produce plausible substitute data. |
| Mixed-grain billing and observed-state data | Can inflate revenue or customer counts. Freeze grain, date roles and group keys and reconcile independently under representative filters. |
| Synthetic design and sparse research support | Can imply commercial performance or expose small cohorts. Preserve denominators, label evidence as synthetic and use approved suppression and explanation rules. |
| Binary review copies and cached imports | Could expose data or reduce change traceability. Keep local caches, exports and binary reviews outside Git and review text project diffs. |
| Future shared service or licensing | Distribution would require separate access, licensing and retention decisions. Current proposal uses local review. |

The owner decisions in §1 resolve initiation, page scope, initial source,
authoring format, distribution boundaries and quality-gate order. The
BI-DR register records conditional approval of the historical architecture
and scoped Registry reuse. Local governance is approved. Research fields
and cohorts, historical exports and WP-11.3 remain deferred. The approved
Windows fixture proof and reference performance workload remain future
verification activities.
