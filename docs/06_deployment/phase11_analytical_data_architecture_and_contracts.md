# Phase 11 analytical data architecture and contracts

**Document ID** · NCI-DASH-002\
**Version** · 0.1\
**Status** · Accepted and completed with documented limitations\
**Work package** · WP-11.2, Analytical Data Architecture & Contracts

## 1. Authority and scope

**PHASE 11 — POWER BI DASHBOARD DEVELOPMENT: IN PROGRESS.**

BI-PO-001–007 authorise specification work following acceptance of the
WP-11.1 planning baseline. The four DASH-PO architecture decisions continue
to apply. The accepted Phase 10 checkpoint
`922528a90270c5df79e56868163d66839bd48d29` matched local `main`,
`origin/main` and live GitHub `main`. The index was clean. The Phase 11
documentation at intake comprised the unstaged roadmap update and the
untracked WP-11.1 planning baseline and WP-11.2 draft.

The proposal uses NEDS v1.1 and the existing 14-phase alignment. Source
contracts, historical facts and scientific claims remain governed by the
accepted Phase 01–10 evidence. The dashboard contracts are new derived
interfaces. Owner approval is required before implementation. Research
field and cohort approval is required before any research dataset is
created or released. Scope is local synthetic review.
[Owner decisions](phase11_power_bi_project_definition.md#project-owner-decisions),
[Implementation roadmap](../07_project_management/implementation_plan_and_roadmap.md#24-phase-11-dashboard-development),
[Phase 10 acceptance](phase10_api_architecture_and_contracts.md#project-owner-acceptance),
[Customer Data Contract v1.1](../04_data/customer_data_contract.md),
[Fieldwise Cloud business specification](../04_data/synthetic_business_model_specification.md).

## 2. Source inventory and verification

### Historical and descriptive inputs

| Source | Classification and inspection | Proposed dashboard use |
|---|---|---|
| Fieldwise Cloud seed-42 `customers.csv`, `subscriptions.csv`, `subscription_snapshots.csv`, `usage_monthly.csv`, `invoices.csv` | No complete original package was found in the authorised development locations. The single BI-DR-012 reconstruction reproduced all five accepted files byte for byte. | Verified historical source for 1 April 2021 through 31 March 2024. Any dashboard transformation remains subject to separate authorisation. |
| Typed Fieldwise episode, billing, snapshot and usage evidence | Retained from the same verified reconstruction. Invoice cadence and conservative availability come from matched scheduled charges and timestamps. Usage bounds and availability and the snapshot evidence timestamps are omitted from the CSV projections. | Supply identity, temporal and cadence checks for the historical facts. Keep the Registry, event evidence and internal record references out of dashboard imports. |
| Phase 05 feature bundle | Existing and verified. `data/processed/phase05-fieldwise-final/` version 2, `fieldwise-episode-features-v1`. The manifest, observations, predictors and prediction-eligibility files matched the audit fingerprints. | Corroborate coverage and point-in-time design. Predictor rows, episode observation rows and outcomes are excluded from dashboard input. |
| Descriptive dashboard bundle | Proposed and unimplemented. No dashboard-ready bundle was verified. | Executive Overview and Customer Analytics. This is the first implementation priority after contract approval. |
| Misata, UCI and any additional external data | Deferred under BI-PO-003. Distinct native grains, identities and currency semantics remain in the source governance record. No new inspection of their data files was needed for this contract. | Outside the baseline report. |
| Live client inputs and protected data | Unavailable to this scope. | Excluded from projections, markets, comparisons and refresh. |

The Phase 05 manifest supplies historical **reference fingerprints**. A later
producer must verify the delivered bytes against its own approved source
manifest. A different Registry can allocate different canonical episode
identifiers. A separate approved replay identity and logical reconciliation
are required in that case, without substituting the old hashes.

| Reference CSV | Accepted rows | Recorded SHA-256 |
|---|---:|---|
| `customers.csv` | 1,000 | `73245c1aab1315904ae6843ed79584229a969903377d8a1b2d787a6db2b2e7b4` |
| `subscriptions.csv` | 1,200 | `9416d3713d4065b4a40640db6e51c1f53f89a3b8a446816599d092972c9f0d17` |
| `subscription_snapshots.csv` | 18,661 | `6e38c94f3faaa923571d26c21e62a618be9e7afb61b16ff1f6ff9e7beb099360` |
| `usage_monthly.csv` | 16,547 | `a99e3182776e017959c1e6cfda1a9cea6ed0386be0585ba09a973a600699eb2a` |
| `invoices.csv` | 14,787 | `0a2cafb9a9710e1406c32d5f8f8e54151f7cc3b221fced7d104494382e9b595e` |

[Phase 02 quality requirements](../04_data/data_quality_specification.md),
[Phase 03–04 reference and acceptance](../07_project_management/implementation_plan_and_roadmap.md#16-phase-03-final-technical-review),
[Phase 05 evidence](../07_project_management/implementation_plan_and_roadmap.md#18-phase-05-point-in-time-feature-engineering),
[Reference producer](../../src/nowa_customer_intelligence/data/eda_inputs.py),
[Projection and internal fields](../../src/nowa_customer_intelligence/data/synthetic/projection.py),
[Accepted ingestion headers](../../src/nowa_customer_intelligence/data/ingestion/header_inspection.py),
[Source governance](../04_data/data_sources_and_governance.md).

### Research inputs and disclosure

Paths below are relative to the locally retained `data/processed` root.
Manifest or report verification establishes provenance only. Every proposed
research export in §5 is **restricted, pending field-level and cohort approval**.

| Proposed export | Retained artefact and source schema | Inspection and binding |
|---|---|---|
| `churn_evaluation` | `phase06-research/results/baseline.json`, `advanced.json`, `manifest.json`. Candidate records contain validation metrics, with selected frozen metadata and `design.support.validation` in the accepted advanced report. | Both reports matched the retained manifest and earlier fingerprint inventory. Bind both source digests, the frozen report model fingerprint and the approved development-validation protocol. |
| `clv_evaluation` | `phase07-clv-research/results/report.json` and manifest. The writer and accepted specification expose `frozen.name`, `scores[name].validation`, `design.support.validation` and `validation_mae_interval`. The writer's `validation` list has row-level values and is excluded. | Report presence confirmed. Manifest and `frozen.json` matched the earlier fingerprint inventory. The mixed-partition report contents remained unopened. Its manifest records SHA-256 `16a2dccc2d909cb192b6ef62a5ac97bdb35b92f690fe25c891873b7d26d63123`, which matches the earlier inventory. Verify the saved bytes and design binding at the authorised data gate. |
| `rfm_summary` | `phase08-segmentation-research/report.json`, paired protocol, design and manifest. The writer exposes `rfm[].date`, `methods`, `per_dimension`, `agreement`, `compared`, and `nominee`. Accepted coverage and nomination evidence also exists in the Phase 08 record. | Report presence confirmed. Manifest, protocol and `rfm_boundaries.json` matched the earlier fingerprint inventory. The mixed research report contents remained unopened. Its manifest records SHA-256 `33877323b89c683aa29a31398d990250220d54724571e16a13f7e699ec8dcd99`, which matches the earlier inventory. Bind report, protocol and design at the authorised data gate. |
| `xai_attribution` | `phase09-explainability-research/churn.json`, `clv.json`, `protocol.json`, `compatibility.json`, `manifest.json`. The reports contain model identity, reference populations, `global.mean_absolute`, `primary.reconciliation` and scale-specific TreeSHAP reconciliation evidence. | All four retained digests matched. Bind the chosen report and protocol digests, each recorded model fingerprint and the reviewed explanation method. No model binary is required. |
| Phase 10 retained-evidence release | Restricted under API-07. The accepted API contract is an independently gated interface. | Excluded from the dashboard input. No release was authorised or created. |

[Phase 06 protocol](../05_ml/phase06_churn_evaluation_protocol.md),
[Phase 07 economic definition](../05_ml/phase07_clv_economic_definition_and_validation.md),
[Phase 08 negative nomination](../05_ml/phase08_segmentation_scope_and_validation.md#formal-limitations),
[Phase 09 validated outputs](../05_ml/phase09_explainability_scope_and_validation.md#executed-research-and-validated-outputs),
[Phase 10 evidence boundary](phase10_api_architecture_and_contracts.md#approved-provenance-and-evidence-catalogue).

## 3. Shared schema, lineage and relationship rules

Each table named below has a matching `<dataset_id>.csv` in its approved
bundle. The proposed initial version of each dataset contract is `1.0.0`.
Field tables give exact proposed column order. **Required** means
non-null. **Nullable** means an empty CSV field represents unknown,
inapplicable or a suppressed value under its governing contract.

| Type | Wire representation and unit |
|---|---|
| Text or enum | UTF-8 non-empty text with exact case, approved vocabulary for enums. Keys are opaque text. Hashes are 64 lower-case hexadecimal characters. |
| Date | `YYYY-MM-DD`, UTC calendar role where sourced from a timestamp. Calendar dates carry no timezone conversion. |
| UTC instant | ISO 8601 with `Z`. Manifest keeps source precision. No subsecond timestamp is required in the report model. |
| Integer or boolean | Base-10 signed 64-bit integer, non-negative for counts. Booleans use `true` or `false`. |
| GBP | Non-negative base-10 fixed decimal with exactly two fractional digits for historical amounts. Source money uses Python `Decimal`. Values and aggregate bounds must fit Power BI fixed decimal. Monthly amounts use GBP/month. |
| Statistic | Finite decimal text retaining saved scalar precision. Map to a Power BI decimal number for display, with precision and units recorded. Integer-valued statistics require exact integers. Preserve signed values where the metric allows them. |

Derive reporting account and episode keys from the verified Fieldwise
ownership mapping. Require an authoritative source account per episode,
the existing canonical episode identifier and a uniquely attributable
invoice identifier. Allocate independent typed prefixes and deterministic
ordinal keys from lexically ordered, case-preserved authoritative keys
within a declared bundle scope. Document source entity, authority,
scope, order and mapping algorithm version. Keep the private mapping
outside the report and source control. Keys are local to the bundle.
A successor remains a new episode under the same verified account. In a
fresh Registry replay, compare logical facts through the authoritative
mapping. Raw identifiers, UUIDs and Registry data stay out of exports.
[Canonical identity ADR](../03_architecture/adr_episode_identity_and_identifier_management.md).

| Relationship | Cardinality and filter direction |
|---|---|
| `account.account_key` to `episode.account_key` | One-to-many, account to episode. |
| `episode.episode_key` to each historical fact's `episode_key` | One-to-many, episode to fact. Historical facts carry no parallel account foreign key. |
| `calendar.calendar_date` to `invoice_issue.issue_date`, `episode_snapshot.snapshot_date`, `episode_usage_month.month_start` | One-to-many per fact, calendar to fact. For usage, aggregate by whole calendar month. Use role-specific calendar copies where independent page filters are required. |
| Account creation and episode start or end date attributes | Validate against the relevant calendar bounds. No additional active path through the shared fact-date dimension. Use dedicated roles or explicit filters for inception cohorts. |
| Research metric, RFM and attribution tables | Separate, self-contained facts with no customer, episode, financial or shared historical-date relationship. Restrict filters to fields provided by the applicable research contract. |

Reject duplicate primary keys, including identical duplicates, before
aggregation. Repeated account observations and valid distinct episodes
retain their original grain. Detect case collisions under the Windows
model collation before loading. Avoid cross-fact row joins, bidirectional
relationships and many-to-many shortcuts. Group and reconcile each fact
before displaying values together. Compare dates using the documented
role rather than inferring it from a column name.

## 4. Historical dataset contracts

BI-DR-001 approves the architecture of all six datasets below with
conditions. Their implementation remains deferred under BI-DR-006.
Their classification is **local synthetic descriptive**. Every delivery uses the source and
export fingerprints, version binding and manual refresh in §7–8. Use the
Fieldwise reference coverage, with table-level bounds and any deliberate
omission in the manifest.

### `account` and `episode` — population dimensions

`account` has one authoritative account at extraction. It is sourced from
`customers.csv` (`customer_id`, `created_at`) and the validated scoped
authority. `episode` has one established canonical subscription episode,
sourced from `subscriptions.csv` and its establishment and lifecycle
evidence (`subscription_id`, `customer_id`, `start_date`, `end_date`).
Use typed date fields, require resolved ownership and exclude current
status and plan attributes from historical cohort filters. Optional
demographics remain outside the initial contract.

| Dataset | Field | Type | Nullability | Unit or rule |
|---|---|---|---|---|
| `account` | `account_key` | Text | Required | Primary key from the scoped account mapping. |
| `account` | `created_date` | Date | Required | Source creation date. Serves account inception cohorts. |
| `episode` | `episode_key` | Text | Required | Primary key from the canonical episode mapping. |
| `episode` | `account_key` | Text | Required | Foreign key to `account`. Exactly one known owner. |
| `episode` | `start_date` | Date | Required | Verified establishment date. On or after account creation. |
| `episode` | `end_date` | Date | Nullable | Recorded episode end where present. Never before start. Unknown is blank. |

Count distinct account keys or episode keys within the selected population
or specified fact cohort. Date slicers on a fact do not implicitly filter
the population dimensions. Test two episodes for one account, a valid
successor, a broken owner reference, duplicate keys and rejected late or
impossible lifecycle bounds.

### `calendar` — descriptive date roles

One date per row, primary key `calendar_date`, generated from the certified
reference start and end dates in the provenance record. A UTC calendar
has every day in the inclusive interval, even if a fact has no records
that day. Month labels are calendar attributes. Calendar completeness
alone cannot attest that the underlying feed was complete.

| Field | Type | Nullability | Unit or rule |
|---|---|---|---|
| `calendar_date` | Date | Required | Primary key, unique and contiguous. |
| `month_start` | Date | Required | First calendar day of the month. |
| `month_end` | Date | Required | Last calendar day of the month. |
| `calendar_year` | Integer | Required | Gregorian year, equal to the year of `calendar_date`. |

Test boundary dates, leap day, month ordering and exact alignment with
every fact's date key. This dimension has no additive measures.

### `invoice_issue` — dated gross invoice issuance

One included and uniquely issued invoice. Source columns are
`invoices.csv` `invoice_id`, `subscription_id`, `invoice_date`, `amount`
and `currency`, validated against the typed `ScheduledCharge`, its episode
ownership and issue availability evidence. The charge supplies issue
cadence. The published fact is as known at the fixed extraction cut-off.
Use date-only issue instants at UTC midnight and require matched occurred,
effective and available evidence at or before that cut-off.

| Field | Type | Nullability | Unit or rule |
|---|---|---|---|
| `invoice_key` | Text | Required | Primary key from the unique authoritative invoice. |
| `episode_key` | Text | Required | Foreign key to the episode that owns the issue. |
| `issue_date` | Date | Required | Invoice issue date and calendar foreign key. |
| `issue_cadence` | Enum | Required | `monthly` or `annual`, from the scheduled charge at issue. |
| `gross_issued_gbp` | GBP | Required | Exact original face amount in GBP. Literal zero is valid. |

Reject missing money, non-GBP, negative or unclassified corrective facts,
bad dates, unsupported cadence, duplicate invoices, charge mismatch or
orphan ownership. Do not silently reinterpret void or refund statuses as
adjustment amounts. Test repeated episode values, multiple invoices in
one period, annual prepay, zero issues, mismatched events and inclusion at
both date boundaries. Aggregate solely over the qualified invoice grain.

### `episode_snapshot` — historical subscription state

One canonical episode at a UTC snapshot date. Composite primary key
`(episode_key, snapshot_date)`. Source is `subscription_snapshots.csv`
(`subscription_id`, `snapshot_date`, `subscription_status`,
`recurring_revenue`, `currency`, `billing_frequency`) and the typed
`SnapshotRecord` with `observed_at`, `occurred_at`, `effective_at` and
`available_at`. Use the observation's historical state with no
master-record backfill or implicit carry-forward across gaps.

| Field | Type | Nullability | Unit or rule |
|---|---|---|---|
| `episode_key` | Text | Required | Foreign key to episode. |
| `snapshot_date` | Date | Required | Observation date and calendar foreign key. |
| `subscription_status` | Enum | Required | `active`, `trial`, `cancelled`, `expired`, `suspended` or `paused`, from the observed snapshot. |
| `contract_cadence` | Enum | Nullable | Historical `monthly` or `annual` contract cadence. |
| `monthly_contract_gbp` | GBP | Nullable | Monthly-normalised contractual amount, GBP/month. Currency must be GBP for a populated amount. |

Allow commercial nulls only when the source has no usable commercial
state. Verify coherence of the complete typed commercial bundle and
that all evidence timestamps are at or before observation. Sum eligible
active recurring amounts only for one explicit snapshot date and report
their coverage. Multiple selected snapshot dates require a per-date
series or a blank total. Test duplicate coordinates, differing master
state, late evidence, missing commercial fields and repeated snapshots.

### `episode_usage_month` — usage and coverage

One canonical episode per calendar month with an established service
period intersecting that covered month, at the fixed extraction cut-off.
Composite primary key `(episode_key, month_start)`. Build the eligible
grid from the verified paid-service interval, beginning at paid activation
and ending immediately before effective termination, if present. A full
month requires that interval to cover every day through the month's last
day within the certified source window. The extraction cut-off bounds
ongoing intervals and determines which evidence is available. Left
join at most one `usage_monthly.csv` row by episode and month, using
`subscription_id`, `usage_month`, `active_users`, `total_users`,
`sessions_count` and `events_count`. Match the typed `UsageRecord` with
inclusive `period_start`, `period_end` and `available_at`. Validate the
label inside those bounds and derive the reporting month from that label.
Source observations through February 2024 and eligible March periods
have different availability states. No account-month unions are implied.

| Field | Type | Nullability | Unit or rule |
|---|---|---|---|
| `episode_key` | Text | Required | Foreign key to episode. |
| `month_start` | Date | Required | First UTC day of the labelled reporting month, calendar foreign key. |
| `coverage_status` | Enum | Required | `observed`, `partial`, `awaiting_reporting` or `missing_or_unavailable` under the rules below. |
| `active_users` | Integer | Nullable | Count within one qualifying observed episode-month. |
| `total_users` | Integer | Nullable | Count within the same observation. If present, at least `active_users`. |
| `sessions_count` | Integer | Nullable | Observed sessions for the qualifying episode-month. |
| `events_count` | Integer | Nullable | Observed events for the qualifying episode-month. |

Classify partial service or a partially bounded record first. For full
months classify as `observed` only with one complete row available by the
cut-off and all three core counts (active users, sessions and events).
Otherwise classify as `awaiting_reporting` if the verified publishing
convention or recorded availability establishes a future release.
Use `missing_or_unavailable` for the remaining full months. Mark all
four counts null for a non-observed row. Structurally absent months with
no known service overlap are outside the grid. Use whole calendar month
filters. A successor has an independent row where it overlaps a month.
Test source-to-grid row reconciliation, phase lag, partial periods,
absent rows, zero counts, late availability, duplicates and any
inconsistent source evidence. Source usage-row counts and the derived
coverage denominator are separate controls.

[Snapshot and usage evidence types](../../src/nowa_customer_intelligence/data/synthetic/observations.py),
[Billing types and catalogue](../../src/nowa_customer_intelligence/data/synthetic/billing.py),
[Historical issue and ownership evidence](../../src/nowa_customer_intelligence/models/clv/history.py).

## 5. Research dataset contracts and field review

The field tables below are allowlist **candidates**. Every field or field
group in each row has the recorded review status **Pending**. For group
rows, the release register must record a separate decision for each named
field. A research export may contain only the fields and row scopes
explicitly approved by the Project Owner. A denial affecting a required
field blocks the dataset until the contract is revised and reapproved.
Never generate actual values for restricted fields as part of the
projection. Keep each dataset separate and report missing or withheld
data as unavailable. No dataset in this section has been created.

### `churn_evaluation` and `clv_evaluation`

Two separate datasets using the layout below. One row is one model role,
named evaluation partition, approved cohort and metric in a specific
experiment. Primary key `(experiment_id, model_role, partition, cohort_id,
metric_id)`. No foreign key to an operational entity. Use the accepted
development-validation partition only. Restrict v1 to the full cohort for
each model and metric. Cadence and other cohort error comparisons require
separate disclosure and evidence review, including their denominators.

| Field | Type | Nullability | Source, unit and constraints | Disclosure |
|---|---|---|---|---|
| `experiment_id` | Text | Required | `nci-phase06-v1` or `fieldwise-clv-v1` in its own table. | Pending |
| `model_role` | Enum | Required | `frozen` or `baseline`. Baselines are the accepted training-prior churn dummy and the CLV training median. | Pending |
| `model_id` | Text | Required | Recorded candidate identity or baseline name. | Pending |
| `model_sha256` | Text | Nullable | Required for the frozen model from approved metadata. Blank for a baseline without a verified fingerprint. | Pending |
| `partition` | Enum | Required | `development_validation` only. | Pending |
| `cohort_id` | Enum | Required | `all` only in v1. | Pending |
| `metric_id` | Enum | Required | Saved metric identifier from the lists below. | Pending |
| `metric_value` | Statistic | Nullable | Accepted scalar, or blank with `value_status` explaining its absence. | Pending |
| `unit` | Enum | Required | `ratio`, `rows` or `GBP`, selected by metric. | Pending |
| `value_status` | Enum | Required | `available`, `undefined` or `withheld`. Require a value only when available. | Pending |
| `support_rows` | Integer | Required | Count of evaluated observations in the same approved cohort. | Pending |
| `support_accounts` | Integer | Required | Count of distinct evaluated accounts in that cohort. | Pending |
| `positive_accounts` | Integer | Nullable | Churn positive account count where approved, blank for CLV. | Pending |

**Churn.** Preserve eligible subscription episodes at UTC observation,
qualifying termination in `(t, t+30 days]` and complete follow-up for a
negative. Development-validation observations are in April–August 2023
with the protocol's exclusive maturity boundary. Proposed metric IDs are
`average_precision`, `roc_auc`, `precision`, `recall`, `f1`, `brier`,
`tn`, `fp`, `fn`, `tp`. Confusion counts are rows at the saved
model-specific research threshold. Compare the same cohort when a
baseline metric is available. Record partition dates and threshold policy
in the reviewed evidence metadata. The 717 rows are from 205 accounts,
eight positive. Weak ranking and insufficient confirmation support must
be visible. The unscored holdout supplies no data to this export.

**CLV.** Preserve `future_6m_issued_gbp` at canonical account and UTC
month-end observation grain. The outcome sums qualified gross GBP issues
in `(t, t+6 calendar months]`, with the approved end-of-month clamp and
maturity rule. Preserve the frozen clipped forecast in the reported error
definition and retain distinct mature zeros and incomplete outcomes.
Validation uses January and February 2023 month ends, with 355 observations
from 180 accounts. Map the saved keys `MAE`, `RMSE`, `Median AE`,
`Bias` and `R²` to `mae`, `rmse`, `median_ae`, `bias` and `r2`,
respectively. The first four use GBP. Bias is prediction minus outcome.
`r2` is dimensionless and may be undefined or negative. Omit thresholds,
customer forecasts, raw reserve summaries and fields implying cash,
recognition, profit, margin, discounting or full lifetime value.

For both tables filter by experiment, model role or approved cohort only,
without projection-time recalculation. Test exact scalar and support
reconciliation, stable metric ordering, zero versus undefined, model
identity, and rejection of unapproved partitions or dimensions. Average
neither ratios nor loss measures across records or partitions. Row and
account support repeat as metadata and have no summation.

### `rfm_summary` — approved financial profiles and nomination

One aggregate statistic per Phase 08 observation cut-off, method,
dimension, category and metric. Primary key
`(observation_date, method, dimension, category, metric_id)`.
No customer foreign key. Scope dates to the fit, validation and subsequent
descriptive assessments on 31 March 2023, 31 December 2023 and
31 March 2024, respectively. Adopt the verified `(t−12 months, t]`
UTC financial window, whole days for recency, invoice counts for
frequency, exact gross issued GBP for monetary input, and the accepted
frozen band rules and cadence support. The export is an aggregate
projection of accepted evidence, without reapplying score boundaries
to a population or deriving a new analytical result.

| Field | Type | Nullability | Source, unit and constraints | Disclosure |
|---|---|---|---|---|
| `observation_date` | Date | Required | Approved `rfm[].date` or accepted coverage observation. | Pending |
| `method` | Enum | Required | `traditional`, `cadence_aware`, `coverage`, `comparison` or `nomination`. | Pending |
| `dimension` | Enum | Required | `recency`, `frequency`, `monetary`, `eligibility`, `agreement` or `status` per the metric grouping. | Pending |
| `category` | Text | Required | Approved individual RFM band (`1`, `2`, `3`), accepted coverage disposition or `all`. No individual combination or cluster label. | Pending |
| `metric_id` | Enum | Required | `account_count`, `agreement_count`, `compared_count` or `operational_nomination`. | Pending |
| `account_count` | Integer | Nullable | Accounts. Populated for approved count rows. | Pending |
| `support_accounts` | Integer | Nullable | Verified population denominator for approved count rows, including common supported accounts for agreement. | Pending |
| `nomination_status` | Enum | Nullable | `no_operational_model_nominated` only on the authorised final status row. Source `nominee=null`. | Pending |

Candidate row combinations are method (`traditional` or `cadence_aware`),
financial dimension and single band for `account_count`. Use
`coverage/eligibility` with `visible`, `eligible` or `short_history`
for the accepted population counts. Use `comparison/agreement/all` for
same-cut-off agreement and compared counts, and `nomination/status/all`
once at the final cut-off. The reviewed field and scope register controls
which combinations may be released.
Suppress unapproved count rows rather than assigning them zero. Reconcile
within one non-overlapping approved partition of an aggregate, with the
eligible population and withheld groups identified where release permits.
Test the accepted negative finding, duplicate rows, unknown support,
mixed-cadence restrictions and rejection of any label or individual
assignment payload.

### `xai_attribution` — frozen explanation aggregates

One approved statistic for a model, explanation method, output scale,
reference, sample and optional analytical term in the Phase 09
development evidence. Primary key `(model_id, method, output_scale,
reference_id, sample_id, term_id, statistic_id)`. No entity foreign key.
The v1 sample is the approved development protocol. Global ranks and
reconciliation diagnostics have different samples. Bind the sample and
its support from the source that actually underlies each statistic.

| Field | Type | Nullability | Source, unit and constraints | Disclosure |
|---|---|---|---|---|
| `model_id` | Enum | Required | `churn` or `clv`. | Pending |
| `model_sha256` | Text | Required | Retained frozen fingerprint in `model.sha256`. | Pending |
| `method` | Enum | Required | `interventional_treeshap_original_features` or `grouped_shapley_clipped_predictor`. | Pending |
| `output_scale` | Enum | Required | `class1_probability`, `class1_log_odds` or `clipped_issued_gbp`. | Pending |
| `reference_id` | Text | Required | Approved protocol identifier for the recorded primary background. | Pending |
| `sample_id` | Enum | Required | `global_development` or `additivity_check`. | Pending |
| `term_id` | Text | Required | Approved original feature or financial block label, or `all` for diagnostics. | Pending |
| `statistic_id` | Enum | Required | `mean_absolute_attribution`, `max_abs_additivity_error` or `additivity_failures`. | Pending |
| `statistic_value` | Statistic | Required | Saved finite scalar, non-negative. Failure counts are exact integers. | Pending |
| `unit` | Enum | Required | `probability_contribution`, `log_odds`, `GBP` or `rows`, according to scale and statistic. | Pending |
| `support_rows` | Integer | Required | Rows in the exact source sample. | Pending |
| `support_accounts` | Integer | Nullable | Distinct accounts when available for that exact sample. No inferred count. | Pending |
| `background_accounts` | Integer | Required | Recorded account support for the selected background. | Pending |

Use Phase 09 `global.mean_absolute` only for the primary churn probability
and CLV grouped GBP output. Preserve churn log-odds reconciliation as a
separate diagnostic from `tree_explanations.raw.original.reconciliation`.
A log-odds global ranking is outside v1 because the documented primary
global summary uses probability. Do not derive it from row attributions.
For CLV use Account lifecycle, Invoice history and cadence, Contract
snapshots and Calendar on the final clipped predictor. Exclude raw and
pre-clip compatibility outputs. Additivity residual and
failure rows use their own reconciliation support. Do not mix units,
normalise between scales or publish individual examples. Labels must
describe model behaviour and uncertainty without claims of causality.
Test the method and scale pairs, term allowlist, sample sizes and
fingerprints. Reject case rows, unsupported scales and feature arrays.

### Disclosure control record

The proposed `disclosure.json` is bundle control metadata, excluded from
the report model. Each release entry has required text keys
`dataset_id`, `field_name`, `contract_version` and `scope_id`
(experiment, partition, cohort or cut-off and method or scale as applicable).
Together they are unique. Record required `status` (`pending`, `approved`
or `denied`), required `classification` and `audience`, optional
`approval_ref` and UTC `approved_at` (required for `approved`), and
required `rule_ref` for disclosure and suppression. A released file's
manifest binds a digest of the approved control record. Approve cohort
support and suppression, including differencing and drill-through, before
projection. Pending, missing or denied entries block generation for the
affected scope. Raw research reports, per-row inference, attribution
vectors and protected inputs are outside every export allowlist.

## 6. Financial reconciliation and future DAX reference

BI-DR-011 approves these historical reporting definitions. Distinguish the
full extraction population, account creation cohorts, established episode
inception cohorts and fact-qualified populations. Reactivation retains the
account and creates a separate canonical episode. Blank termination dates
do not establish historical activity. Use explicit UTC date roles, inclusive
reporting dates within certified coverage and half-open paid-service
intervals. The invoice view uses issue date and evidence known by the fixed
extraction cut-off. Show snapshot amounts at one certified date and identify
the expected active population and usable active observations separately.
Usage coverage uses certified full episode-month opportunities.

| Measure | Independent Python reference definition |
|---|---|
| Gross issued GBP | On validated source invoices, select distinct eligible invoice IDs in the inclusive issue-date range, verified GBP and available evidence at the bundle cut-off. Sum exact `Decimal` face amounts. Join an owner only through the unique episode mapping. One full annual invoice stays on its original issue date. Treat negative invoices, unsupported corrections or currency and missing amounts as errors. Payment status or date does not alter the issued amount. |
| Invoice count | Count the same unique invoice set, including a literal zero issue. A complete feed and admissible period with no issues gives count 0 and £0.00. An uncertified or missing feed produces unavailable. Amount and count remain blank outside certified coverage. |
| Distinct accounts | Count scoped source account keys. Use population inception dates for inception cohorts. For an invoice or usage cohort count owners of distinct qualifying fact episodes. The report must label which population applies. |
| Subscription episode count | Count unique canonical episodes in the selected cohort. Multiple valid episodes of the same owner contribute separately. Active snapshot counts use the observed active state on one date. |
| Historical cadence | Group included invoices by the typed charge's issue cadence. If requested at account and selected-window grain, classify an account by the set of its included issue cadences as monthly, annual or mixed. A verified period with no issues has no observed cadence. Never substitute the current subscription setting. |
| Observed usage coverage | Independently enumerate full episode-month opportunities from certified lifecycle and calendar facts. Count observed complete and available rows and divide by the sum of observed, awaiting and missing or unavailable full-month opportunities. Report partials separately. A zero denominator is undefined and displayed blank. Never sum precomputed percentages. |
| Financial reporting window | Select calendar dates within certified coverage. Show the fixed source extraction cut-off independently from issue dates and refresh timestamp. Mark any slice crossing uncertified coverage as incomplete and leave headline totals blank until the range is within coverage. Snapshot monthly contractual totals are GBP/month at one approved active snapshot date. |

The historical reference controls are **1,000 accounts**, **1,200 episodes**,
**14,787 invoices** and **£1,566,111.80** gross issued. Monthly comprises
14,273 issues and £1,127,567.00. Annual comprises 514 issues and
£438,544.80. The historical snapshot control is £77,056.60 per month for
1,000 active episodes at extraction with usable amounts. Preserve the
separate input controls of 16,547 usage and 18,661 snapshot rows. A coverage
projection with derived opportunities needs its own reconciled census.
The independent validator reads approved source facts and exports
separately and compares exact pennies and counts at full scale and by
selected month, cadence and reactivation cohort. Include negative
fixtures for duplicates, window boundaries, blanks, non-GBP, corrections,
and invoices joined to several usage periods. Compare ratios from their
constituent counts, with display rounding applied only afterwards.

Gross issuance is separate from cash collected, recognised or net revenue
and profitability. Credits, refunds, taxes, settlement and FX require
approved source policies before any expansion. The historical and CLV
contracts share gross issuance semantics and have different time and
observation grains. [Accepted historical and CLV semantics](../05_ml/phase07_clv_economic_definition_and_validation.md#historical-measure).

## 7. Exchange format, manifest and versioning

Recommend **UTF-8 CSV with a JSON manifest** for the first supported
Windows refresh. CSV is inspectable and uses existing Python support.
Specify a comma delimiter, quoted fields as needed, UTF-8 without BOM,
one exact ordered header, LF line endings, deterministic primary-key
ordering and explicit null and date handling. Use exact two-decimal GBP
strings and verify range and precision before import. Treat Parquet as a
future option for larger data. It preserves machine types and compresses
well, and the Power Query connector supports local files. Adoption would
require a justified Python writer dependency and a Windows round-trip
check of decimals, dates and nulls. A local approved bundle has no database
or runtime API dependency.
[Power Query CSV reference](https://learn.microsoft.com/en-us/powerquery-m/csv-document),
[Parquet connector](https://learn.microsoft.com/en-us/power-query/connectors/parquet),
[Power BI data types](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-data-types).

The proposed `manifest.json` is a closed, independently verified
envelope. Unknown keys, versions, fields, types or path spellings fail
validation. The entire approved release has one immutable bundle version.
The manifest carries the authoritative schema for the current bundle,
with detailed constraints defined by the approved contract documentation.

| Required metadata | Type, uniqueness and rule |
|---|---|
| `manifest_version`, `bundle_version`, `bundle_id`, `scope` | Positive integer, versioned text, unique text ID, and enum `fieldwise_descriptive` or `fieldwise_research`. One scope and immutable identity per bundle. |
| `generated_at_utc`, `source_cutoff_utc`, `producer_git_sha`, `producer_version`, `identity_mapping_version` | Two UTC instants and three text fields. Use approved Git revision, transformation and private mapping versions. For research, the mapping version is null and cutoff refers to the approved source evidence cut-off. |
| `sources[]` | Unique source entries of required `source_id`, `source_version`, `source_sha256`, `source_kind` and `approval_ref` as text. Include the authorised scenario/configuration or research protocol, source bytes and relevant evidence manifests in the lineage. Never include protected source inventory. |
| `datasets[]` | One row per `dataset_id` with `contract_version`, `export_path`, `export_sha256`, `size_bytes`, `row_count`, typed `coverage_start`, `coverage_end`, `coverage_role`, `source_ids[]`, `classification` and `disclosure_status`. Text fields except integer byte and row counts and ISO dates. Coverage is table-specific. Path is the fixed basename. Reject unexpected files. Every source reference resolves. |
| `datasets[].columns[]` | Exact ordered schema with required text `name`, `type`, `unit` and Boolean `nullable`. Use explicit enums, key and cross-row constraints from the declared contract version. |
| `datasets[].evidence` | Null for descriptive inputs. Research requires text `protocol_id`, `scope_id`, `entity_grain`, `measurement_basis` and `limitation_ref`. Include nullable `threshold_policy_ref` for churn confusion metrics. References point to accepted research definitions. No restricted artefact path or individual result belongs here. |
| `approval_ref`, `disclosure_sha256` | Text approval reference for all bundles. Research requires digest of the independently approved disclosure control record. Descriptive bundles use null for the disclosure digest and require approved local synthetic scope. |

Use major schema versions for incompatible changes. A compatible approved
addition receives a new declared contract version and must be explicitly
accepted by the consumer before use. Data refresh without schema change
gets a new immutable bundle ID and version. Canonically order data by
key and manifest keys by the agreed writer rules. A repeated generation
against the same source identity, inputs, fixture and producer must
yield byte-identical dataset CSVs and identical hashes. Generation
timestamps vary separately. Bind the manifest SHA-256 to a separately
recorded owner-approved delivery reference. A manifest beside a file is
insufficient if both have been replaced. Keep stage directories private,
validate the complete exact inventory before promoting a new read-only
bundle, and retain the prior approved bundle until sign-off.

## 8. Power BI consumption and local data handling

1. The approved Linux Python process will write to a local ignored area
   such as `data/processed/phase11-power-bi/<bundle_id>/` or an approved
   non-repository equivalent. Keep immutable descriptive and approved
   research bundles separate. Generated CSVs, manifests that contain
   private locations, local approvals, raw reports, mappings and caches
   stay outside Git. The existing `data/*` ignore rule covers generated
   data under that root. Verify ignore coverage for any later authoring
   cache or PBIX location before creation. Commit schemas, contracts and
   non-sensitive definitions only under separate authorisation.
2. Transfer only the authorised bundle to a controlled Windows local
   directory and verify the exact manifest approval and hashes there
   before refresh. Use a local verifier with the same contract rules.
   Restrict initial access to the Project Owner acting as Data Steward.
   Record refresh and handoff events, verifier outcome and bundle version
   without logging record values. Retain the current verified bundle and
   one rollback version until replacement approval. A later authorised
   reviewer-copy workflow must enforce the proposed maximum of 30 days.
   Reviewer copies remain outside this task. See BI-DR-005 for export and
   distribution boundaries.
3. Power BI Desktop Import uses one parameterised, Windows-accessible
   root per approved bundle and an expected ID and accepted contract
   version. Power Query performs explicit UTF-8 parsing, exact header
   checks, explicit `en-GB` typing, date and nullable-field handling
   and metadata checks. Interpret `YYYY-MM-DD` fields as calendar
   dates. Preserve UTC metadata as unambiguous ISO text or parse as
   UTC before loading a datetime. Import monetary columns as fixed
   decimal after Python validation. Blank, zero and unsupported
   coverage remain separate. Avoid automatic identity or amount type
   inference and silently coerced nulls.
4. Hash verification is a required pre-refresh step outside Power Query.
   Power Query checks bundle ID, version, inventory and schema, then
   fails the affected refresh on mismatch or conversion error. Never
   blend versions. With no current trusted data show unavailable. A
   previously approved retained copy may be used only with its visible
   last verified version and failure status. Never claim a successful
   refresh from unchanged cached data.
5. Python remains responsible for eligibility, monetary and scientific
   calculations and validated sampling context. Validate semantic
   relationships before final DAX. Use DAX for explicit reviewed
   aggregation and filter context. Run final refresh and visual checks
   on a supported Windows build under BI-PO-005 and BI-PO-007. The
   workflow must operate with FastAPI stopped. Desktop authoring,
   PBIP/PBIX, Power BI Service, live customer connections and external
   distribution remain outside this work package.

## 9. Required tests and WP-11.2 acceptance matrix

**Passed** records evidence for the named design or scope check.
**Failed** means a required check was attempted and its criterion was
unmet. **Not Tested** marks an execution check deferred to its authorised
increment. **Pending Owner Approval** identifies a decision that the
specification leaves with the Project Owner. Dependent work stays gated
until its required checks and approvals pass.

| Gate | Status | Evidence or dependency |
|---|---|---|
| BI-CT-01 — Traceable source provenance | Passed | §2 identifies the producer, schema and traceable fingerprints for each source and labels evidence gaps. Phase 07–08 mixed-report bytes were left unopened. Their recorded digests were corroborated against the earlier audit inventory. |
| BI-CT-02 — Explicit analytical grain | Passed | All ten proposed datasets define a single grain, primary key and date or experiment role. Control records declare table and field identities. |
| BI-CT-03 — Field definitions and types | Passed | The schema tables give ordered names, meaning, types, nullability and units. Financial amounts and scientific statistics have distinct precision and validity rules. |
| BI-CT-04 — Approved financial semantics preserved | Passed | Gross issuance is in GBP at invoice issue grain, monthly contractual amounts are separate and the six-calendar-month CLV target is unchanged. §6 defines source-level reconciliation and accepted reference totals. |
| BI-CT-05 — Reporting aggregation rules | Passed | BI-DR-011 approves the specification definitions in §6, including the populations, UTC date roles, fixed-extraction invoice view, snapshot coverage and usage denominator. Dashboard implementation and DAX verification remain separate gates. |
| BI-CT-06 — Relationship design prevents duplication | Passed | §3 defines dimension-to-fact cardinality, keeps research separate and excludes fact-to-fact joins. Later model tests must prove counts and amounts under fan-out, duplicate key and reactivation fixtures. |
| BI-CT-07 — Testable data-quality constraints | Passed | Schema, uniqueness, foreign keys, validity, coverage, completeness and reconciliation checks have expected outcomes, including rejection of invalid input. Each dataset names its targeted tests. |
| BI-CT-08 — Reproducible versioning specified | Passed | §7 defines immutable versioned bundles, ordered outputs, manifest and digest binding, and the scope of byte-stable replay. |
| BI-CT-09 — Export integrity, replay and reconciliation | Not Tested | Future implementation must verify complete source and output inventories, exact fingerprints and rows, independent Python totals and byte replay under a fixed Registry. Reject missing, corrupt, swapped or incompatible bundles. |
| BI-CT-10 — Power BI refresh assumptions documented | Passed | §8 specifies Windows Import, path parameters, verification before refresh, type, null and version checks, and failure behaviour without a FastAPI runtime dependency. |
| BI-CT-11 — Windows and DAX execution | Not Tested | BI-DR-007 approves a future fixture-only proof. A supported Windows build must create, save, reopen and refresh PBIP and verify basic semantic compatibility and version-control suitability. Final DAX reconciliation remains a later gate. |
| BI-CT-12 — Disclosure classifications and restrictions | Passed | Historical contracts are classified local synthetic descriptive. Every research field is marked pending and restricted content is excluded from the allowlists and refresh paths. |
| BI-CT-13 — Research fields and cohort release | Pending Owner Approval | BI-DR-003 and BI-DR-004 defer disclosure. The field and cohort controls must receive a separate approval before any research projection. |
| BI-CT-14 — Protected reserve boundary | Passed | Verification used the accepted development artefacts, retained manifests and accepted project records. No protected reserve path was opened or used as an input. |
| BI-CT-15 — Change and implementation boundaries | Passed | Verified the Phase 10 baseline and clean index. This work changed documentation only. WP-11.3, exports, report artefacts and semantic models were not started. |
| BI-CT-16 — Implementation authorisation | Pending Owner Approval | BI-DR-015 formally accepts the specification. Historical analytical export implementation requires separate Project Owner authorisation under BI-DR-006. WP-11.3 remains pending authorisation under BI-DR-008. |

For invalid source, schema, permission, provenance or reconciliation,
fail the affected bundle validation before promotion. Report the dataset,
rule and bounded error category. Keep restricted values, paths and
identifiers out of messages. Suppression decisions remain auditable
through the control record. Date, aggregate and provenance tests shall use
synthetic fixtures and accepted scalar controls without running training,
scoring or research notebooks.

## 10. Proposed implementation sequence

The sequence follows the approved gate order in BI-PO-007. Each work
package needs its own authorisation and required preceding evidence.

| Work package | Proposed work | Gate before dependent work |
|---|---|---|
| WP-11.2 closure | The verified historical evidence and approved definitions support specification acceptance. Research disclosure remains deferred. | Accepted and completed with documented limitations under BI-DR-015. |
| WP-11.3 — Semantic model design | Pending separate authorisation under BI-DR-008. The future Windows proof approved under BI-DR-007 has its own fixture-only scope. | Accept the contract conditions and record the Windows proof or local PBIX fallback before relying on the authoring format. |
| WP-11.4 — Data preparation and Power Query | Implement the descriptive Fieldwise bundle first after approval. Exercise validation, transfer, inventory checks and fail-closed local refresh. Prepare research projections only for separately approved fields and cohorts. | Verified, reconciled data and refresh. Validate historical and research relationships in the imported model. |
| WP-11.5 — DAX measures | Agree filter-context rules and compare reviewed DAX results with independent Python reference calculations. | Exact reconciliation of counts and pennies, and approved handling of ratios, nulls and coverage. |
| WP-11.6–11.8 — Report pages | Deliver the descriptive views first. Gate each research page on approved evidence, disclosure and its own acceptance checks. | Verify source version, method, grain, definitions, limitations and visible unavailable states. |
| WP-11.9–11.10 — Assurance and acceptance | Run supported Windows visual and refresh tests, check export permissions and verify reproducibility and documentation. | Record results and request formal Project Owner acceptance. A failed gate blocks dependent work. |

## 11. Risks, open approvals and dependencies

| Risk or dependency | Effect and control |
|---|---|
| Historical source preservation and Registry scope | The controlled reconstruction verified the reference files and identities. Preserve the verified bundle, pin its digests before any authorised use and retain the original Registry unchanged. An additional replay or different namespace requires separate authorisation. |
| Mixed research evidence or outstanding field approval | A research page may remain unavailable. Verify only authorised evidence and suppress unapproved fields and cohorts. |
| Incorrect relationships or date context | Invoice amounts and distinct counts can inflate. Validate the semantic model, then independently reconcile full and filtered controls. |
| Windows toolchain, local permissions or cache handling | Failure blocks refresh or risks unintended retention. Prove the selected Desktop build and format and approve local storage, access, retention and review copies. |

The Project Owner accepted the verified reference and specification under
BI-DR-014 and BI-DR-015. Separately approve any future replay, historical
export implementation or WP-11.3 initiation. Research pages remain
unavailable pending disclosure approval.
The exact Windows build and approved fixtures remain to be verified in
the future proof. No execution gate has been advanced.

## 12. Project Owner decision register

The Project Owner approved the following dispositions. BI-DR-015 records
formal WP-11.2 specification acceptance. The conditions and deferrals
govern implementation and disclosure. WP-11.3 remains pending authorisation.

| Decision | Status | Approved disposition and conditions |
|---|---|---|
| BI-DR-001 — Historical Analytical Contracts | Approved with Conditions | Approve the architecture of `account`, `episode`, `calendar`, `invoice_issue`, `episode_snapshot` and `episode_usage_month`. Implementation requires verified source availability, approved population and date-filter definitions, invoice issuance and financial reconciliation rules, referential integrity, correct episode ownership, snapshot population and usage denominator definitions, and explicit source lineage. The contracts are not yet implementation-ready. |
| BI-DR-002 — Registry Reuse | Approved with Conditions | Approve scoped, read-only reuse of `data/interim/phase05-fieldwise.sqlite`. Verify the approved SHA-256 `28525cb869dcfdb62a64e255f5dad715e1f0cdbed5887269e6f61d72ae0eea90` before use. Preserve the immutable original and canonical namespace. Keep writable producers away from the original, reconcile the six Registry-only episode IDs and fail closed on missing or inconsistent mappings. Population reconstruction and replay require separate authorisation. Protected reserves remain excluded. |
| BI-DR-003 — Research Disclosure | Deferred | All 34 proposed fields remain Pending Owner Approval. No research aggregate exports may be generated or published. |
| BI-DR-004 — Research Cohorts | Deferred | Research cohort disclosure remains unauthorised. Retain the proposed development-only cohorts for future review. Exclude protected reserves and unsupported partitions. |
| BI-DR-005 — Local Data Governance | Approved | Initially restrict access to the Project Owner acting as Data Steward. Use Linux preparation, controlled local transfer and Windows authoring. Store generated datasets, temporary reports and caches outside Git. Retain the current verified bundle and one rollback version until replacement approval. Enforce the proposed 30-day maximum for any later authorised temporary reviewer-copy workflow. Create no reviewer copies now. Power BI Service publication, cloud synchronisation, public sharing, external distribution and live customer data are outside scope. Only specifically approved historical synthetic exports may be considered in future implementation. |
| BI-DR-006 — Historical Export Implementation | Deferred | Implementation requires separate Project Owner authorisation after contract and source conditions are resolved. |
| BI-DR-007 — Windows PBIP Proof | Approved for Proof Only | Authorise a future proof with approved synthetic fixtures on supported Power BI Desktop. Verify PBIP creation, save, reopen, data refresh, basic semantic-model compatibility and version-control suitability. PBIX remains the approved local fallback. The proof does not authorise publishing or distribution and was not started in this task. |
| BI-DR-008 — WP-11.3 | Deferred | WP-11.3 remains pending. Semantic-model implementation and report authoring remain unauthorised. |
| BI-DR-009 — Canonical NEDS v1.1 | Approved | Designate `docs/standards/NA_Engineering_Development_Standard_NEDS_v1.1.md` as the canonical repository copy, SHA-256 `e2b165a04a1213c2367968cc8938fafadfab27fa19bdd4570b84a918606a025c`. Preserve the approved text byte for byte. Exclude the project-management duplicate and Windows metadata sidecar from the checkpoint. Leave them untracked and unstaged. |
| BI-DR-010 — AGENTS.md Adoption | Approved with Corrections | Prepare `AGENTS.md` for formal adoption. Preserve its purpose and project guidance. Clarify reserve access and work-package authorisation, cite the canonical NEDS, roadmap and Phase 11 specifications, and distinguish the failed raw interventional CLV TreeSHAP reconciliation from other configurations. |
| BI-DR-011 — Historical KPI Definitions | Approved | Approve full account, creation and fact-qualified cohorts, and episode establishment, inception, ownership and qualified populations. Use explicit UTC calendar roles and boundaries, gross GBP issued by the selected date as known at fixed extraction, certified single-date snapshot populations and monetary coverage, and full episode-month opportunity denominators with distinct observed, partial, awaiting-reporting and missing or unavailable states. |
| BI-DR-012 — Controlled Historical Reconstruction | Approved with Conditions | Authorise one run only if a complete original source package cannot be recovered from an authorised location. Use the accepted generator, seed, configuration, scenario, cutoff and canonical scope with an isolated verified copy of the retained Phase 05 Registry. Preserve the original byte for byte. Exclude reserves, training, inference, scoring and research replay. Stop on mandatory failure and require all equivalence evidence before claiming an exact reproduction. |
| BI-DR-013 — WP-11.2 Acceptance Boundary | Approved | Keep WP-11.2 open until source provenance, historical identity, financial controls and historical contract conditions are resolved and the Project Owner formally accepts the work package. WP-11.3 remains pending. |
| BI-DR-014 — Historical Reference Acceptance | Approved | Formally accept the reconstructed Fieldwise Cloud historical development reference as an exact verified reproduction. The checksums, identity reconciliation and financial controls in §13 govern the accepted package. |
| BI-DR-015 — WP-11.2 Formal Acceptance | Approved | Accept and complete WP-11.2 with documented limitations. Acceptance covers the analytical architecture, six historical contracts, source provenance, identity definitions, historical reporting semantics and specified controls. Implementation and disclosure remain separately gated. |
| BI-DR-016 — Controlled Documentation Checkpoint | Approved | Authorise one documentation-only commit and a standard fast-forward push recording BI-DR-011–016, the historical integrity evidence, formal WP-11.2 acceptance, remaining restrictions and the Phase 11 roadmap status. Exclude source data and implementation work. |

[Canonical NEDS v1.1](../standards/NA_Engineering_Development_Standard_NEDS_v1.1.md),
[Repository agent instructions](../../AGENTS.md).

## 13. Historical reference reconstruction evidence

**Classification — Exact Historical Reference Reproduction, accepted under
BI-DR-014.** Authorised
development locations had no complete original package. One execution of
`fieldwise_reference()` used seed 42, the baseline TEMPORAL scenario,
Contract v1.1, business model v0.2 and PD-006. Its reference cutoff was
31 March 2024 at 23:59:59.999999 UTC. The run matched the retained
Phase 05 generation parameters, dependency versions and RNG stream
algorithm. BASIC and TEMPORAL succeeded and all 13 required development
acceptance gates passed.

All five CSV row counts and SHA-256 values matched §2. The canonical
typed evidence digest was
`a9ed8d2a7c64839cce867652c326a86839d83ee193fe31fedf57908c97b7e09a`,
matching Phase 05. The retained typed groups cover lifecycle and ownership,
snapshots, usage and scheduled charges from the same run. Independent
checks verified the source headers, unique keys, foreign keys and temporal
bounds.

The original Registry and isolated copy retained the BI-DR-002 digest.
All 1,200 mappings and their audit records were unchanged. All 200
reactivations preserved separate episode identities and account ownership.
The 18,661 reconstructed snapshot keys matched the retained Phase 05
candidate inventory across 1,194 episodes. The six additional Registry
episodes terminated on or before their first eligible month-end and had
no snapshot candidate. No new mappings were allocated.

The accepted controls below include exact decimal financial reconciliation.
The derived dashboard usage denominator remains implementation evidence.

| Control | Accepted result |
|---|---:|
| Customers | 1,000 |
| Subscription episodes | 1,200 |
| Reactivations | 200 |
| Unique invoices | 14,787 |
| Gross issued GBP | £1,566,111.80 |
| Monthly invoices | 14,273 |
| Monthly gross issuance | £1,127,567.00 |
| Annual invoices | 514 |
| Annual gross issuance | £438,544.80 |
| Subscription snapshots | 18,661 |
| Monthly usage source records | 16,547 |
| Active episodes at extraction snapshot | 1,000 |
| Monthly contractual GBP at extraction snapshot | £77,056.60 |

The private, Git-ignored local package is
`data/interim/wp11-2-historical-reference.DkZGlP/`. It contains the five
source CSVs, canonical typed JSON lines, provenance, Registry reconciliation
and verification records, and the isolated copy. The verification record
SHA-256 is `b42d52e5ebca93d72912f73fca2054f66aec42ef34f0cc091b5b6c9d14371258`.
The accepted original Registry fingerprint is
`28525cb869dcfdb62a64e255f5dad715e1f0cdbed5887269e6f61d72ae0eea90`.
The acceptance checkpoint verified the retained evidence without executing
another reconstruction. Keep the package and its evidence outside Git.

## 14. Formal WP-11.2 acceptance

**WP-11.2 — ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS.**

BI-DR-015 formally accepts the specification for `account`, `episode`,
`calendar`, `invoice_issue`, `episode_snapshot` and `episode_usage_month`.
Their approved grains, keys, relationship rules, financial semantics,
reporting populations, temporal definitions and coverage requirements
remain authoritative. The verified source and identity evidence is in §13.
The BI-DR-011 KPI definitions remain in force.

The sixteen-criterion matrix records **12 Passed**, **2 Not Tested**
and **2 Pending Owner Approval**. BI-CT-09 dashboard export generation,
integrity, replay and reconciliation remain untested. BI-CT-11 Windows
authoring, PBIP/PBIX verification, refresh and DAX remain untested.
BI-CT-13 retains all 34 research disclosure fields and associated cohorts
pending approval. BI-CT-16 retains separate historical export
implementation authorisation. Specification acceptance completes WP-11.2.
It grants no implementation or research disclosure authority. WP-11.3
remains pending authorisation.
