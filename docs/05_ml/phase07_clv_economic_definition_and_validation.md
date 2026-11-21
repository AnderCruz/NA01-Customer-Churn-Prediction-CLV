# Phase 07 CLV economic definition and validation

## Authority and gate

BO-02, FR-022–025 and AC-009 require future customer value on a documented revenue
or contribution-margin basis over a defined horizon, with customer-level and
aggregate views. The [contract](../04_data/customer_data_contract.md), ADR-009/010
and PD-006 establish financial fields, canonical episode attribution and temporal
snapshot requirements. The [synthetic business specification](../04_data/synthetic_business_model_specification.md)
describes the fictional catalogue and leaves the official CLV estimator open.
The [modelling strategy](modelling_and_evaluation_strategy.md) proposes alternatives.
The Project Owner subsequently approved CLV-PO-001 to CLV-PO-004 for the fictional
experiment. These decisions resolve the earlier forecast gate and are recorded below.

NEDS v1.1, the repository business and requirements records, architecture
decisions, contract, Phase 03–06 records and accepted roadmap entries were
reviewed. The standalone Charter and complete approved 14-phase roadmap were
unavailable. Phase numbering follows the owner brief and repository roadmap.
The available records contain no different approved Phase 07 notebook names.

## Historical measure

Measure GBP issuance observed within the fictional source window. Each unique
invoice belongs to one canonical episode and exactly one account through the
episode. Use a date-only issue instant at UTC midnight, consistent with Phase 05,
and require matching internal billing evidence whose occurrence, effective and
availability times all precede or equal observation. The evidence's timestamp
acts as a conservative availability bound. The payment status and dates do not
determine the issued amount. Contract CSVs lack an independent issuance availability
timestamp. The current internal evidence convention is specific to Fieldwise.

Use only established episodes known at observation. Include known issuance from
both active and completed episodes in account history. A reactivation creates a
new canonical episode linked to the same account. Both invoice streams remain
individually attributable. Independently established concurrent episodes can
contribute distinct invoices without duplication. The reference has no concurrent
active episodes, so it cannot validate commercial coverage of concurrency.
Account tenure is days since the source account creation date. It is distinct
from episode tenure, continuous billing tenure and lifetime history.

A missing invoice feed yields an unavailable measure. A present feed with no
visible invoice yields an observed sum of £0.00 and undefined average and recency.
A literal zero issue is separately counted. Recent or missing coverage limits
interpretation of all three. Counts reflect visible invoices rather than invoice
completeness. Window-bounded totals do not claim that earlier or unobserved
history had zero value. Signed reversals and mixed currencies are outside the
non-negative GBP baseline. The snapshot's monthly-normalised contractual amount
is a separate point-in-time measure, conditional on known activity and a usable
snapshot. Summing it across active episodes gives a snapshot total in GBP per
month. Annual prepay creates lumpy issuance, regardless of the normalised rate.

| Measure | Evidence and disposition |
|---|---|
| Historical issued invoice amount | `invoice_id`, `subscription_id`, `invoice_date`, Decimal `amount`, GBP `currency` and internal availability evidence. Implemented. |
| Snapshot recurring amount | Eligible historical snapshot's monthly-normalised GBP amount. Implemented as a separate measure. |
| Collected cash | Payment date and status exist, but settlement, reversals, partial payments and allocations need independent evidence. |
| Recognised or net revenue | Requires accounting treatment and service periods, adjustment, tax and allocation evidence. |
| Gross or contribution margin | Requires approved cost scope and reliable cost allocation. |
| Discounted or total lifetime value | Requires an approved value basis, time horizon, future event scope and discount/terminal policy. Historical issuance alone cannot supply those. |

## Approved owner decisions

| Decision | Approved policy |
|---|---|
| CLV-PO-001 | Canonical customer/account target `future_6m_issued_gbp`. Six calendar months of gross issued GBP as recorded. Undiscounted, without margin, cash, recognition or lifetime extrapolation. |
| CLV-PO-002 | Include all canonical episodes owned by an eligible account, including legitimate successors and concurrent episodes. Determine eligibility from known account creation. Activity is optional. No invented credit, reversal, tax, payment or profit treatment. |
| CLV-PO-003 | Certify complete issuance through horizon and availability by ascertainment before fitting. Retain confirmed positives and zeros, immature, incomplete, unresolved and ineligible outcomes as distinct states. Unknown amounts stay null. |
| CLV-PO-004 | Forward temporal and disjoint account evaluation, independent CLV reserve, training-only preprocessing and selection by validation MAE in GBP. Report RMSE, median absolute error, signed bias, aggregate error, R² where meaningful, and cohort errors. |

## Target and availability

Observation is a UTC month end. In (t, t+6 calendar months], add six to the UTC
month, retain the day when valid and otherwise clamp to the last valid day.
Preserve UTC time. For example, 31 August 2023 at month end shifts to 29 February
2024 at month end. Date-only issue instants are UTC midnight. An issue exactly at
t is historical and an issue at the horizon end is included. The ledger validates
invoice identity and canonical ownership before indexing. Future episodes are
available only to the outcome ledger.

The accepted fictional generator schedules every in-scope issue through its
cutoff, and its pipeline and integrity gates validate the exported inventory.
This supplies the bounded completeness attestation for the reconstructed
fictional source. The calculation requires matching evidence and its occurrence,
effective and availability timestamps. Observations with a horizon after cutoff,
missing attestations, late evidence beyond ascertainment or unresolved
adjustments stay unknown. The contract alone does not attest to completeness of
external feeds or their adjustments. There is no arbitrary lateness allowance.

## Customer predictor specification

The separate CLV registry in `models/clv/features.py` records each field's name,
definition, units, source and nullability. The four monetary amounts are Decimal
GBP or Decimal GBP/month before numerical modelling. Days and counts are
non-negative integers. The remaining fields are category strings with levels
defined by source state, cadence mix or UTC month 01–12. The model receives no
identity or target fields.

Account creation and lifecycle must be known by t. Invoice amount, count,
mean, recency and cadence use only visible issues. Recent issuance uses the
current and preceding 89 UTC dates, bounded by the source window. A missing feed
makes billing quantities null, while an empty visible ledger has zero count and
amount but no recency or mean. Active snapshot totals require a usable amount
for every known active episode, with a separate coverage count. No active episodes
means zero recurring snapshot total. Usage and plan features were omitted from this
single-plan reference because account-level usage aggregation is not yet defined
and the plan has no variation. The Phase 05 feature contract remains unchanged.

## Frozen experiment `fieldwise-clv-v1`

| Partition | Population | UTC observation dates | Exclusive maturity boundary |
|---|---|---|---|
| Training | Seed 42, accounts in fixed hash buckets 0–69 | Month ends June 2021–June 2022 | 1 January 2023 |
| Validation | Seed 42, hash buckets 70–99 | January and February 2023 month ends | 30 September 2023 |
| Independent reserve | Seed 731, separate fictional namespace and temporary Registry | 30 September 2023 month end | Source extraction end, 31 March 2024 inclusive |

The first eight bytes of SHA-256 of `fieldwise-clv-v1:<customer_id>`, interpreted
as an unsigned big-endian integer modulo 100, assign development accounts.
Repeat snapshots, predecessor episodes and successors share a group. Partition
eligibility checks outcome maturity before the next boundary. Historical lookbacks
can overlap in calendar time. Distinct synthetic namespaces identify different
populations, and canonical episode UUID sets were checked for overlap. The
seed-2027 churn reserve, Phase 06 scored partitions as independent evidence, and
churn probabilities were excluded.

The pre-fit floors were 150 training accounts and 100 accounts for each
evaluation partition, with at least 30 positive and 15 zero-target accounts and
at least 15 with visible evidence of each cadence in every partition. These
are minimum support checks for an exploratory synthetic audit and avoid reliance
on only a few annual or zero-value cases. They do not certify statistical power.
All three passed. Saved design evidence records partition fingerprints, source
inventories, seed, windows, menu and environment. The report and model freeze
have local checksums. Preserve the scored reserve result, and do not rerun the
same confirmation for selection.

The fixed menu is training median, Ridge (alpha 10), Random Forest (100 trees,
depth 8, leaf minimum 15), and histogram gradient boosting (100 iterations,
15 leaves, leaf minimum 25, learning rate 0.06, L2 regularisation 1 and no early
stopping). Estimator seed 42 governs stochastic fits. Median imputation with
indicators, numeric scaling and unknown-safe one-hot encoding fit on training
only. Clip negative forecasts to zero. The contractual schedule benchmark was
deferred because renewals and retention are unsupported. The model with lowest
validation MAE wins, with a one-penny tolerance in declared menu order. The
winning fit is frozen before a single reserve inference. No alternative was
scored on that reserve.

## Findings and deliverables

Histogram Gradient Boosting was nominated at £58.27 validation MAE versus
£112.96 for the training median and £59.25 for Random Forest. Forest had lower RMSE,
so boosting's MAE choice does not imply the smallest large errors. The nominated
model's £16.45 training MAE shows a substantial in-sample advantage. Reserve
MAE was £51.57 with +£18.42 bias over 802 distinct accounts. No reserve baseline
comparison was performed. These are synthetic findings from a single later
landmark and catalogue, with no evidence of real-client generalisation.

[Notebook 07](../../notebooks/04_clv_modelling/07_clv_historical_value_and_baselines.ipynb)
retains the historical analysis and adds approved target maturity and baseline evidence.
[Notebook 08](../../notebooks/04_clv_modelling/08_clv_predictive_models_and_validation.ipynb)
renders checksum-verified local artefacts, financial errors and cohort diagnostics.
Both keep source outputs cleared and perform no model fitting during rendering.
