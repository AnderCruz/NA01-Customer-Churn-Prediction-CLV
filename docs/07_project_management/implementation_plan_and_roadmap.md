# Implementation Plan and Roadmap

**Document ID:** NCI-PM-001  
**Version:** 0.2  
**Status:** Draft for review

## 1. Delivery approach

Work will proceed in small, reviewable phases. Each phase must produce an artefact and pass its acceptance checks before the next phase begins.

The initial planning estimate is 12–16 weeks of individual development effort, subject to scope, data quality, and time availability. This is a planning range, not a delivery commitment.

## 2. Phase alignment

The approved 14-phase Project Roadmap governs phase order and acceptance. The consolidated Phase 03 review brief confirms the following sequence and status. The complete approved roadmap and standalone Project Charter were unavailable in the reviewed project references.

| Phase | Status |
|---|---|
| 01 — Repository & Development Environment | Completed |
| 02 — Data Foundation & Data Quality | Completed |
| 03 — Data Acquisition | Accepted and completed with documented limitations. |
| 04 — Data Understanding & EDA | Accepted and completed with documented limitations. |
| 05 — Feature Engineering | Accepted and completed with documented limitations. |
| 06 — Churn Modelling | Accepted and completed with documented predictive limitations. |
| 07 — CLV Modelling | Accepted and completed with documented limitations. |
| 08 — Customer Segmentation | Accepted and completed with documented limitations and negative model nomination. |
| 09 — Explainable AI | Accepted and completed with documented limitations. |
| 10 — API Development | Accepted and completed with documented limitations. FastAPI and Pydantic for the approved internal, read-only Research & Analytics API. |
| 11 — Dashboard Development | In progress. WP-11.1 accepted. WP-11.2 accepted and completed with documented limitations. WP-11.3 accepted and completed with documented implementation limitations. WP-11.4 pending authorisation. Microsoft Power BI with Power Query, DAX and Python-prepared analytical datasets. |
| 12 — MLOps | Pending. Retains its approved scope and position. |
| 13 — Docker & AWS | Pending. Retains its approved scope and position. |
| 14 — Testing & Documentation | Pending. Retains its approved scope and position. |

### 2.1 Historical draft phase table

The earlier draft is retained below for traceability. Apply the approved phase sequence above to the implementation records in this document.

| Phase | Workstream | Main activities | Deliverables |
|---|---|---|---|
| 0 | Product definition | Review business case, scope, requirements, architecture | Approved documentation baseline |
| 1 | Repository and environment | Create GitHub repository, package structure, virtual environment, quality tooling | Reproducible development environment |
| 2 | Data acquisition | Record dataset sources, download and validate development data | Raw data inventory and source register |
| 3 | Data understanding | EDA, data-quality analysis, label feasibility | EDA and data-readiness report |
| 4 | Feature engineering | Point-in-time snapshots, feature pipeline, leakage checks | Versioned feature pipeline |
| 5 | Churn modelling | Baseline, candidate models, temporal evaluation | Churn model report and artefact |
| 6 | CLV modelling | Select suitable CLV method and forecast horizon | CLV model/report |
| 7 | Segmentation | RFM/behavioural features, clustering, profiling | Segmentation report |
| 8 | Explainability and risk | SHAP, risk bands, revenue exposure calculations | Explainability and risk outputs |
| 9 | Dashboard | Executive, churn, CLV, segments, model performance | Functional dashboard |
| 10 | API and persistence | Add API and database if justified by workflow | Scoring service and persistence layer |
| 11 | MLOps and packaging | MLflow, Docker, CI, monitoring hooks | Reproducible release candidate |
| 12 | Pilot readiness | Security/privacy review, client mapping, operational runbook | Pilot deployment package |

## 3. Suggested initial schedule

| Period | Focus |
|---|---|
| Weeks 1–2 | Documentation approval, repository, environment |
| Weeks 3–4 | Data acquisition, EDA, data-readiness |
| Weeks 5–6 | Feature engineering and churn baseline |
| Weeks 7–8 | Churn candidate models and evaluation |
| Weeks 9–10 | CLV and segmentation |
| Weeks 11–12 | Explainability and dashboard |
| Weeks 13–14 | Testing, Docker, MLOps foundations |
| Weeks 15–16 | Pilot-readiness review and documentation |

The schedule may change based on data issues and the decision to build API/database components in the MVP.

## 4. Working method

For each phase:
1. Agree the objective.
2. Review inputs and dependencies.
3. Implement a small increment.
4. Run tests and inspect outputs.
5. Document decisions and limitations.
6. Review acceptance criteria.
7. Commit changes to Git.
8. Confirm whether the phase is complete.

## 5. Git workflow

Suggested branches:
- `main`: stable, reviewed code.
- `develop`: integration branch if needed.
- `feature/<short-description>`: individual changes.
- `fix/<short-description>`: corrections.

Use pull requests for changes that materially affect the product. Keep commits focused and descriptive.

## 6. First implementation milestone

The first coding milestone is not model training. It is a clean repository and reproducible environment with:
- Project structure.
- README.
- Dependency management.
- Configuration approach.
- Logging.
- Basic tests.
- CI workflow.
- Data directories excluded appropriately from Git.

## 7. Definition of done

A phase is complete when:
- Deliverables exist.
- Acceptance checks pass.
- Tests pass where applicable.
- Documentation is updated.
- Known limitations are recorded.
- Changes are committed.
- The next phase's dependencies are understood.

## 8. Synthetic generator Batch 02 implementation record

WP-01 was accepted for configuration and run context after 169 targeted tests passed. Its seven-file local checkpoint is `79d38498e51e51d4e7c2e04e22feef5fb4635fc2`. WP-02 and WP-03 are implemented and tested. The project owner accepted those two work packages under Batch 03 after all 22 targeted tests passed and repository-wide Ruff checks passed.

- **WP-02.** `create_random_stream(master_seed, name, namespace="default")` uses `numpy.PCG64+sha256/nci-stream-v1`. SHA-256 covers the ASCII bytes `nowa.synthetic.stream.v1`, one NUL byte, eight unsigned big-endian seed bytes, the ASCII namespace, one NUL byte and the ASCII stream name. The digest interpreted as an unsigned big-endian integer seeds NumPy's explicit `PCG64` bit generator. Each call creates a fresh generator at its initial state. The seed range is 0 through 2⁶³ − 1. Names and namespaces are bounded lowercase ASCII labels. Replay, a fixed derivation vector, creation-order independence and global state isolation were verified locally on NumPy 2.5.4. Cross-version or cross-platform output equivalence and L1/L2/L3 verification remain with WP-10.
- **WP-03.** `generate_customers(effective)` uses the `customer.created-at` stream in the selected scenario ID namespace. It returns an ordered tuple of immutable accounts with population-local `synthetic-customer-NNNNNN` ordinal IDs, a date sampled uniformly from the inclusive configured history and fictional baseline country `GB`. The date distribution is an engineering assumption. Industry, company size and account status are omitted pending configured assumptions. The supported date window must fit the existing UTC nanosecond representation. The population is held in memory and uniqueness applies within that population. Subscription references and production CSV projection require later work.
- **Evidence.** The consolidated suite passed 843 tests (797 unit and 46 integration), with no failures or skips. WP-02 and WP-03 both reached 100% statement coverage in their modules. Customer populations of 1, 12 and 1,000 records passed the existing customer type normalisation and schema checks. No customer CSV, linked subscription population or multi-dataset validation claim was produced.

## 9. Synthetic generator Batch 03 implementation record

WP-02 and WP-03 were accepted after 22 targeted tests and repository-wide Ruff checks passed. The six-file local checkpoint is `a32c9995cfece871474b51a46070c5dc79a82866`. WP-04 and WP-05 are partially completed and await review of their bounded foundations.

| Requirement | Decision status and implemented boundary |
|---|---|
| Canonical episode ownership and customer relationship | Approved — implementable. ADR-009/010, PD-002 and BDR-001 govern one caller-established episode per supplied UUID and exactly one explicit owning customer. Duplicate UUIDs and missing customer references are rejected. |
| Supplied UUIDs for development | Synthetic-only assumption — explicitly authorised by Batch 03. Validate the supplied standard UUID spelling and value, retain its spelling and check duplicate UUID values irrespective of casing. Generation, persistence and matching are outside this interface. |
| UUID issuance and durable registry | Open — implementation blocked by BDR-013, RPR-015, DD-EP-003 and RPR-016. Select and validate issuance, replay, persistence and lineage mechanisms before generating canonical IDs. |
| Establishment evidence and historical preservation | Approved — implementable at the supplied-fact boundary. Establishment timestamps are explicit, timezone-aware and separately represented. Supplied historical episodes retain their records. Confirmed reactivation requires a separate episode per BDR-002, with automated allocation blocked by BDR-013. |
| Lifecycle transitions, termination evidence and concurrency | Open — implementation blocked by BDR-014 and DD-EP-001/005–007. Status is a supplied category. This interface performs no state replay, termination inference or policy adjudication for concurrent episodes. |
| Snapshot convention and production projection | Not applicable to this batch. BDR-010 and BDR-015 continue to govern unresolved temporal conventions. Existing schemas were exercised on in-memory fixture fields. |
| Fictional commercial arithmetic | Synthetic-only assumption — explicitly authorised. Apply the Fieldwise GBP list prices and 10% annual discount using exact penny amounts. Validate explicit invoice identifiers, dates, non-negative finite Decimal amounts and supplied ownership. |
| Billing schedules, semantic attribution and accounting | Open — implementation blocked by BDR-012, DD-EP-011 and BDR-017. No date, payment status, refund or recognition policy is inferred from an invoice or episode. |

The consolidated suite passed 891 tests (844 unit and 47 integration), with zero failures or skips. The 210 targeted synthetic tests included 47 new unit tests and one new cross-component integration test. Both new modules reached 100% statement coverage. Repository-wide Ruff lint and format, dependency consistency and whitespace checks passed. The integration fixture preserved customer records, passed the existing subscription and invoice schema checks and wrote no files. This evidence covers explicit facts and arithmetic. Full lifecycle, billing histories, policy-based semantic attribution and production projection remain outside the implemented foundation.

### Batch 04 foundation verification

- **WP-04 — Foundation Implemented and Verified; Full WP Pending**
- **WP-05 — Foundation Implemented and Verified; Full WP Pending**

All 48 targeted episode, billing and integration tests passed. Repository-wide Ruff lint and formatting passed. Verification covers supplied UUIDs and ownership, preservation of explicit episode facts, exact GBP catalogue arithmetic and validation of supplied invoice facts. Identity issuance, lifecycle replay, billing schedules and formal full-package acceptance remain pending.

## 10. Synthetic generator Batch 04 vertical slice

The verified WP-04/05 foundations are checkpointed in `20c4cee83553fc07b05f1522934635b2195ec9da`. Full work-package acceptance remains pending.

- **WP-06.** `UsageRecord` and `validate_usage` check explicit inclusive coverage dates, subscription ownership, uniqueness by labelled month, non-negative quantities, user counts, and optional availability against the extraction cutoff. `SnapshotRecord` and `validate_snapshots` check explicit historical status and separate occurrence, effective, availability and observation timestamps. Supported commercial facts use the existing fictional GBP catalogue and monthly-normalised revenue. No monthly convention, lifecycle replay or behavioural distribution is inferred.
- **WP-08.** `project_development_population` checks the declared inventory, customer coverage and supported record relationships, then returns immutable contract-ordered rows. `export_development_csvs` uses exclusive writes in a caller-supplied empty temporary directory. Internal timestamps and periods stay out of contract columns. Missing optional columns are represented by empty values, and unsupported fields fail projection. This interface is for development fixtures only.
- **Evidence.** BASIC succeeded with 2 customers, 2 subscriptions, 1 usage record and 1 invoice across four CSVs. TEMPORAL succeeded with the same records plus 1 historical snapshot across five CSVs. Both passed existing schema, applicable referential-integrity and data-quality gates, including TC-001/002 date ordering. RI-002 was inapplicable to BASIC without snapshots and passed for TEMPORAL. These checks do not establish broader historical correctness, semantic attribution for client sources or model eligibility.
- **Quality.** The targeted synthetic and pipeline suites passed 276 tests. The full suite passed 928 tests (879 unit, 49 integration), with no failures or skips. Statement coverage was 100% for `observations.py` and 97% for `projection.py`. Its uncovered statements are defensive unsupported-type, unsupported-field and missing-required-value guards. Ruff lint and formatting, dependency consistency and whitespace checks passed.
- **Remaining decisions.** BDR-010 requires an explicit monthly snapshot convention and termination-date treatment. BDR-011 requires agreed usage coverage boundaries. BDR-015 governs model observation and availability cutoffs. BDR-013, DD-EP-003, BDR-014 and BDR-012 still block source-generated identity, lifecycle and billing histories. The development slice is ready for technical review. Full WP-06 and WP-08 acceptance remains pending.

### Batch 05 foundation reverification

- **WP-06: Foundation Verified — Full Work Package Pending.**
- **WP-08: Development Projection Verified — Production Integration Pending.**

All 66 observation, projection and pipeline tests passed. Repository-wide Ruff lint and format checks passed. BASIC without snapshots and TEMPORAL with snapshots passed the implemented pipeline gates using temporary fixture exports. Semantic attribution, full historical correctness, model eligibility and production publication remain outside this checkpoint.

## 11. Synthetic generator Batch 05 evidence foundations

WP-06 and WP-08 foundation reverification is checkpointed in `bb855d81131c65dd3a3731d2939a6553b218e98c`. All 66 checkpoint tests passed.

- **WP-07.** Immutable `OutcomeRecord` and `OutcomeEvidence` retain the five supplied internal states, source references, temporal evidence and observation and ascertainment cutoffs. `validate_outcomes` checks unique episode observations and explicit ownership. Structural checks do not establish event qualification, completeness or model eligibility. No binary label, outcome persistence or contract projection is implemented.
- **WP-09.** `validate_synthetic_evidence` reuses the domain validators and checks explicit source bindings, episode lineage, cutoff chronology and feature availability. Its fixed diagnostic categories distinguish passed, failed, not evaluated and blocked by unresolved policy. Canonical allocation, lifecycle replay, billing schedules, monthly conventions, target and eligibility remain policy-blocked. The existing pipeline is unchanged.
- **WP-11.** Isolated one-defect fixtures cover duplicate episode or observation grains, missing ownership, unknown references, contradictory facts, future evidence, incorrect invoice attribution, invalid outcome evidence and unsupported transitions. Tests check rejection and preservation of the valid fixture. The suite covers implemented checks only.
- **Evidence.** The 45 new tests passed. The full suite passed 973 tests (923 unit and 50 integration), with no failures or skips. Both new modules reached 100% statement coverage. Ruff lint and formatting, dependency consistency and whitespace checks passed. An integration fixture passed the existing BASIC pipeline with customer and subscription CSVs while outcome truth remained internal.
- **Remaining work.** BDR-013 and DD-EP-003 govern identity issuance and persistence, BDR-014 governs lifecycle, BDR-012 governs billing timing, and BDR-010/011/015 govern temporal generation. CGQ-006/007/010–012/021 and CGQ-016 govern later outcome certification and eligibility. Full WP-07, WP-09 and WP-11 acceptance remains pending. WP-10 has not started.

### Batch 06 foundation acceptance

WP-07, WP-09 and WP-11 foundations are accepted within their Batch 05 scope after 45 targeted tests and repository-wide Ruff lint and formatting passed. Full work packages remain pending. Supplied internal outcome truth and isolated negative fixtures confer no production outcome or eligibility certification.

## 12. Synthetic generator Batch 06 implementation record

The Batch 05 foundation passed 45 targeted tests and the acceptance evidence is staged. Automatic approval review initially blocked the local checkpoint. The final technical validation brief explicitly authorised it, and the six-file checkpoint was created at `96c8b579ffabd185ee2b007d70d573e816f9e856`.

**Authorised synthetic-only scope.** Fieldwise Cloud Synthetic Baseline v1 uses UUID4 allocations persisted and reused in a local, client- and namespace-scoped SQLite Registry (BDR-013, DD-EP-003, RPR-015/016). Allocations and corrections are transactional. Ambiguous evidence and conflicting keys are rejected. Explicit source-key corrections retire the earlier mapping and preserve audit lineage. Same-Registry replay retains UUIDs. A fresh Registry allocates new UUID4 values.

- **WP-04.** Explicit establishment and paid activation create the first episode. The configured target may add one explicit post-termination reactivation per eligible customer. Renewals continue an existing episode. The development validator checks ownership, event order, history preservation and non-overlap. Trial, pause, suspension and concurrent service remain outside this scenario (BDR-014 and DD-EP-001/005–007).
- **WP-05.** Explicit paid activation anchors GBP monthly or annual advance invoices. Original anniversary days are preserved with short-month clamping. Service periods are half-open and may be clipped at termination without proration. Explicit plan requests take effect at the next boundary. Subsequent payment facts are provided by the fictional scenario and have no automatic lifecycle effect. BDR-012, BDR-017 and DD-EP-011 retain their production or client decision statuses.
- **WP-06.** Usage uses explicit fictional quantity bounds, complete calendar months and a configured reporting lag. Snapshots use UTC month-end and available historical evidence, with catalogue-based monthly-normalised revenue. Partial usage months, unscheduled termination snapshots and retrospective application of late evidence are excluded. Broader temporal conventions and model cutoffs remain open under BDR-010/011/015 and CGQ-020.
- **WP-08/WP-09.** `DevelopmentGenerationRequest` is a separate typed development boundary. It reuses effective configuration without changing schema v1 or WP-01 run semantics. `generate_development_population` retains lifecycle, attribution, billing and availability evidence internally. It reuses development projection and existing pipeline validation. Production policy findings remain blocked, and target and eligibility are outside the evidenced scope.

**Measured baseline.** From 1 April 2021 through 31 March 2024, the seed-42 test generated 1,000 customers, 1,200 episodes (200 explicit reactivations), 14,787 invoices, 16,547 usage records and 18,661 snapshots. BASIC passed without snapshot input and TEMPORAL passed with all five inputs. Both passed existing schema, applicable RI and applicable DQ stages. TC-001 passed and TC-002 was inapplicable. RI-002 passed in TEMPORAL and was inapplicable in BASIC. Scoped Registry, lifecycle, billing and monthly evidence findings passed. Same-Registry replay reproduced all projected rows; a separate fresh-Registry test preserved usage facts while allocating different IDs. Under coverage, the first baseline generation and validation took 7.160 seconds and in-memory replay took 4.693 seconds.

The full suite passed 989 tests (937 unit and 52 integration), with zero failures or skips. New-module statement coverage was 97% for the Registry, 90% for lifecycle and 89% for the development entry point. The extended billing, episode and observation modules reached 100%, 96% and 96% respectively. Uncovered paths include defensive rejection of malformed requests, inconsistent generated facts and uncommon Registry errors. Ruff lint and formatting, dependency consistency and whitespace checks passed. No generated artefacts were added to the repository. This evidence applies to the fictional development scenario. Full work-package and production acceptance remain pending.


### Batch 06 final technical validation

The seed-42 baseline reproduced all five previously recorded counts and 200 reactivations. All seven pipeline stages succeeded in BASIC and TEMPORAL. RI-002 was inapplicable to BASIC and passed in TEMPORAL. TC-002 was inapplicable to both. No pipeline gate failed. The covered run took 5.838 seconds including both workflows, and same-Registry in-memory replay took 3.955 seconds. A fresh Registry produced distinct UUID4 values with matching tested usage, snapshot and billing facts when keyed by authoritative source identity.

The review corrected same-day lifecycle ordering and rejected termination at or before activation. Additional tests verified concurrent Registry allocation, replay and rollback of partial CSV exports without invoking the pipeline or network access. The regression suite passed 993 tests (940 unit and 53 integration), with zero failures or skips. Statement coverage was 97% for Registry, 92% for lifecycle, 89% for development, 100% for billing, and 96% each for episodes and observations. Ruff lint and formatting, dependency consistency and whitespace checks passed.

Technical recommendation is acceptance with documented limitations for the fictional development scope. Production policy, complete temporal and semantic certification, outcome assessment and WP-10 reproducibility certification remain outside the evidence. Project-owner acceptance remains pending.

### Batch 06 limited acceptance

**BATCH 06 — Accepted for Fictional Development Baseline, with Documented Limitations.** The 20 acceptance tests and repository-wide Ruff checks passed. This acceptance covers the tested local Registry, synthetic generation and BASIC/TEMPORAL compatibility. Individual work-package statuses and unresolved decisions are preserved. Production policy, deployment, model eligibility and full reproducibility certification remain outside this acceptance.

## 13. Synthetic generator Batch 07 development evidence

Batch 06 limited fictional-development acceptance was checkpointed in `58043a39ffc5054305880f1e870d4ab10b05a226`. The approved design baseline, data contract, ADRs, product decisions and pipeline interfaces retain their original status and scope.

- **WP-10.** `run_development_with_provenance` captures allowlisted configuration and scenario parameters, a seed reference, the RNG version, runtime dependencies, local Registry context and actual pipeline statuses. `capture_development_integrity` checks exported rows against the projection and records file presence, CSV record counts, sizes, SHA-256 and validation references. For retained exports, capture occurs before and after pipeline validation. `verify_development_integrity` checks the files again without repair. `evaluate_development_acceptance` requires the current file evidence, both pipelines and the scoped semantic and temporal gates. Publication remains inapplicable, and unresolved production policy gates remain visible.
- **Replay.** The same recorded Registry and runtime reproduced the tested IDs and projected rows after reopening. The fresh-Registry test retained tested non-identity facts and issued different UUID4s. Changed effective seed values had distinct provenance references. The byte digests cover actual files and confer no canonical serialisation or L1/L2/L3 certification.
- **WP-11.** Isolated tests rejected duplicate identities, cross-client allocation conflicts, inconsistent lineage and transitions, invalid billing and observations, duplicate or wrongly attributed invoices, missing required files, corruption, partial writes, real pipeline failure, inconsistent inventories and absent integrity evidence. Negative runs did not repair or publish artefacts.
- **Evidence.** The baseline reproduced 1,000 customers, 1,200 subscriptions, 14,787 invoices, 16,547 usage records and 18,661 snapshots. All seven pipeline stages passed in both workflows and all 13 required development acceptance gates passed. SHA-256 and row counts were verified for all five files. The full suite passed 1,019 tests (943 unit and 76 integration), with zero failures or skips. Provenance statement coverage was 95%. Ruff lint and formatting, dependency consistency and whitespace checks passed.
- **Deferred.** Full WP-10 and WP-11 acceptance requires project-owner review. Churn qualification, coverage and ascertainment, censoring, feature eligibility and evaluation splitting remain governed by CGQ-006–016, CGQ-021 and RPR-013/017. This batch generated no training labels and made no production or reproducibility certification claim.

### Batch 07 foundation acceptance

**BATCH 07 — Foundation Accepted with Documented Limitations.** All 29 targeted provenance, integrity, replay, negative fixture and baseline tests passed. All 13 required development gates passed. WP-10 and WP-11 retain partial status. This acceptance is limited to tested fictional development evidence and file integrity.

## 14. Synthetic generator Batch 08 churn experiment

Batch 07 foundation acceptance was checkpointed in `ecd8262ef8a6aec58913879c64fa37778594dab9`. WP-10 and WP-11 retain partial status.

**Fieldwise Cloud — Subscription Churn Experiment v1** (`fieldwise-subscription-churn`, version 1) implements the synthetic-only scope of CGQ-006/007/009–012/021 and RPR-013. It uses canonical episode identity, a configurable 90-day history and 30-day prediction horizon in the test, and caller-supplied UTC observation, ascertainment and extraction cutoffs. Confirmed positives require authoritative termination in the open-left, closed-right horizon and adjudication by ascertainment. Confirmed negatives require explicitly attested complete follow-up through the horizon. Shorter complete follow-up is right-censored. Missing or unresolved evidence is pending. Invalid identity, unsupported historical evidence or an explicit exclusion remains ineligible. Production CGQ, BDR, RPR and DD-EP decisions retain their original statuses.

The in-memory modelling dataset keeps outcome metadata separate from allowlisted predictors. Features use activation, historical commercial snapshots, completed available usage months and issued invoice and payment evidence known by observation. Optional volume and overdue histories remain unavailable for the baseline. The fixture explicitly attests the exhaustive fictional lifecycle ledger. Its per-observation ascertainment cutoff is the earlier of horizon end and extraction. Construction without that attestation leaves unproven negatives pending. Dataset preparation checks current development acceptance and file integrity. It leaves all contractual CSVs unchanged.

The seed-42 baseline produced 18,661 candidates, with 151 confirmed positives, 14,212 confirmed negatives, 895 right-censored, zero pending and 3,403 ineligible for insufficient observation history. Resolved prevalence was 1.05%. Exclusive UTC split boundaries were 1 July 2022, 1 July 2023 and 1 April 2024. Groups stayed in their earliest mature partition. The episode-disjoint split retained 2,010 training rows (311 episodes and customers, zero positives), 2,216 validation rows (379 episodes and customers, 40 positives), and 1,581 test rows (332 episodes, 309 customers and 27 positives). Horizon crossings excluded 966 labelled observations. Earlier group assignment excluded 7,590. The separate customer-disjoint mode retained 2,010, 2,036 and 1,136 rows respectively. No class balance was imposed. The reviewed training partition lacks positive examples, so binary model training readiness remains blocked for this split.

All 16 targeted tests and 1,035 repository tests passed (958 unit and 77 integration), with no failures or skips. Statement coverage was 95% for outcome classification, 96% for historical predictors and 93% for dataset assembly and splitting. Leakage tests covered future termination, payments, usage, snapshots, late corrections and separation of target metadata. Reverse-order reconstruction matched the initial dataset, tampered exports were rejected and the integrated run required no network access. Ruff lint and formatting, dependency consistency and whitespace checks passed. No training or production publication was performed.

### Batch 08 foundation acceptance

**BATCH 08 — Modelling Data Preparation Foundation Accepted with Documented Limitations.** All 16 targeted outcome, feature, split and end-to-end tests passed. Repository-wide Ruff lint and formatting passed. Binary training remains blocked for the reviewed split because the training partition contains zero confirmed positives. The seed-42 fixture and reviewed split are preserved.

## 15. Batch 09 split diagnosis and first synthetic ML experiment

**Status: Archived pre-Phase 06 experimental technical spike.** The preserved baseline and its integration test use the historical Batch 09 synthetic predictor interface. This spike predates Phase 06. The previously scored test partition is development-only, and the results below are historical experimental evidence. The integration test fits models and must be excluded from verification runs that prohibit training.

Batch 08 foundation acceptance is checkpointed in `cfdf92a928fadf96ec3b58ce7511e785df2786a2`. The seed-42 generator, scenario, outcome policy and reviewed split are preserved. The 151 positive observations represent 151 of the 200 terminated episodes. First eligible positive observations occur in September 2022, after the reviewed training boundary of 1 July 2022. The synthetic generator terminates selected initial episodes at the midpoint of their remaining history and establishes a separate later episode. The first simulated terminations occur in October 2022. Training maturity checks and episode grouping operate as designed. In the reviewed split, 7 positives crossed a horizon boundary and 77 were assigned to an earlier episode group. The resolved inventory reconciles to 5,807 assigned and 8,556 excluded observations.

**Selection protocol recorded before fitting.** Review the existing split, followed by forward calendar alternatives with training and validation ends of January/July, April/September, May/October and July/November 2023, with test end fixed at 1 April 2024 UTC. Select the earliest candidate in that order with both classes, valid chronology and at least 30/10/10 independent positive episodes. Boundaries evaluate existing episodes at progressively later cutoffs with explicit label maturity. No model scores enter this selection. The April/September candidate first passes with 66/10/19 positive episodes. Customer-disjoint evaluation is separate. Training-only preprocessing and models compare validation average precision, with a fixed threshold grid selected on validation F1 and higher-threshold tie breaks. The held-out partition is scored only for the selected model and threshold.

**Audit and measured support.** The 49 terminated episodes without positive observations comprise 39 with insufficient observation history and 10 without a snapshot in the horizon. The unchanged alternative split retained 5,902 training observations (66 positives), 559 validation (10 positives) and 900 test (19 positives). Horizon crossings excluded 1,248 and earlier episode-group assignments excluded 5,754. All 15 required approach gates passed, including deterministic reconstruction, predictor isolation, mature labels and independent positive-episode support. Customer disjointness was inapplicable to the selected episode-disjoint evaluation.

**Classical baseline results.** Scikit-learn preprocessing used training-only median imputation, scaling and categorical one-hot encoding. Validation average precision was 0.017889 for the prior dummy, 0.056247 for unweighted logistic regression and 0.054760 for class-weighted logistic regression. The validation-selected unweighted model and threshold 0.005 yielded held-out average precision 0.013676, ROC-AUC 0.236514 and zero precision, recall and F1. The confusion matrix contained 747 true negatives, 134 false positives, 19 false negatives and zero true positives. The predicted positive rate was 14.89%. Class support was sufficient for this engineering exercise, but the held-out result does not demonstrate useful churn discrimination. No scenario variant, resampling, refit on validation, deployment or production modelling policy was introduced.

All 1,036 repository tests passed (958 unit and 78 integration), with zero failures or skips. The new model gate and evaluation module reached 94% statement coverage. The integration test confirmed each candidate fit saw training rows only and held-out scoring occurred once after validation selection. Repository-wide Ruff lint and formatting, dependency consistency and whitespace checks passed.

## 16. Phase 03 final technical review

The fictional Fieldwise Cloud seed-42 development baseline reproduced 1,000 customers, 1,200 subscription episodes, 14,787 invoices, 16,547 monthly usage rows and 18,661 snapshots over the configured 1 April 2021 to 31 March 2024 window. All five CSVs loaded successfully. BASIC succeeded with snapshots omitted, and TEMPORAL succeeded with snapshots present. All seven pipeline stages succeeded in each workflow, and the 13 mandatory development acceptance gates passed. TC-002 was inapplicable to this evidence. Production identity, lifecycle, billing, monthly temporal conventions and target and eligibility policies remain unresolved.

The five exports matched their recorded row counts, sizes and SHA-256 values. A second export in the same environment and with the same Registry produced equal logical tables and matching SHA-256 values for all five CSVs. Fresh-Registry tests showed distinct UUIDs and matching tested business facts when keyed by authoritative source identity. Cross-environment equivalence and formal L1, L2 and L3 certification remain unverified.

### 16.1 Project Owner decision

**Decision: APPROVED — Phase 03 Synthetic-First Data Acquisition Scope.**

The Project Owner explicitly approved Fieldwise Cloud as the primary source for initial development, testing, EDA and experimental modelling. The decision resolves the public acquisition scope question from the technical review. Public dataset identification and technical assessment are complete for the candidates in the [data-source inventory](../04_data/data_sources_and_governance.md). IBM Telco was assessed as a separate churn benchmark. UCI Online Retail and Online Retail II were assessed as transactional analysis candidates. Each has gaps against the subscription-episode contract.

The initial scope decision deferred public dataset integration. The subsequent owner approval in §16.3 authorises two complementary sources for this phase. Other public candidates remain outside the integration scope. Production data sources and client-specific policies require separate approval.

### 16.2 Closure assessment

The implemented contract and scoped development gates are satisfied. The five validated CSVs support Phase 04 EDA once authorised. This assessment applies to the fictional development scope. Production policies, complete temporal validation and formal reproducibility certification remain outside that scope.

The phase sequence is confirmed by the Project Owner's instructions. A standalone copy of the complete approved 14-phase roadmap and the standalone Project Charter were unavailable for independent traceability. The original completed Phase 3.3.1 population specification and its independent approval evidence remain unverified under FDB-001 in the [approved design baseline](../04_data/synthetic_data_generation_design_baseline.md). The tested population anchors are documented there and in the generation rules. These gaps remain documented limitations for the approved initial scope.

**Technical review verdict — Ready for acceptance with documented limitations.** The final owner acceptance is recorded in §16.4.

### 16.3 Complementary public-source integration

The Project Owner authorised Misata B2B SaaS Subscription Analytics and UCI Online Retail II for official acquisition and independent local analytical integration before Phase 03 closure. Both acquisitions and both live source-adapter validations succeeded. Misata supplied 42,240 rows across five native tables with zero duplicate primary keys or orphan account references. UCI supplied 1,067,371 invoice lines across two sheets. The retail adapter reports missing customers, repeated lines, cancellations and signed quantity and price exceptions while retaining all source rows. The [source governance record](../04_data/data_sources_and_governance.md#8-approved-complementary-phase-03-sources) records publisher evidence, licence, provenance, source schemas, quality metrics and verification commands.

The two sources are available through independent Python interfaces for future EDA. Their identifiers remain source-local. Full canonical contract integration, publication, production policies and client-specific processing remain outside this authorisation. Fieldwise Cloud remains the primary development source. The seed-42 baseline counts, BASIC and TEMPORAL results and development gates remain unchanged. The Charter, full roadmap and FDB-001 traceability limitations in §16.2 still apply.

The complementary source integrations are complete for local analytical use. The final owner acceptance is recorded in §16.4.

### 16.4 Project Owner final acceptance

**PHASE 03 — DATA ACQUISITION: ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS.**

The Project Owner authorised acceptance subject to verification. The accepted scope covers synthetic-first acquisition, Fieldwise Cloud generation and validation, public-source assessment, independent Misata and UCI Online Retail II analytical integration, provenance and integrity, and development-data readiness. The verification reproduced the Fieldwise reference counts, both workflows and all 13 required development gates, verified the local public archives and adapter evidence, and passed 1,054 regression tests within the no-training scope.

Public-source identifiers and history remain native to each source. Commercial data-use conditions remain source-specific, and production integration and publication require separate approval. Cross-environment reproducibility remains unverified. The standalone Project Charter, complete approved roadmap copy and original FDB-001 population evidence remain unavailable for independent traceability. Phase 04 implementation follows the local Phase 03 checkpoint.

## 17. Phase 04 data understanding and EDA

EDA began after the Phase 03 checkpoint `86bcf36612bf358fdad8aa3112f08e1c8057d212`. The [three exploratory notebooks](../../notebooks/README.md#phase-04-data-understanding) reconstruct the accepted seed-42 Fieldwise data and analyse Misata and UCI independently through their source-native adapters. Rendered output and temporary Fieldwise exports are outside version control.

- **Customers and episodes.** Of 1,000 Fieldwise accounts, 800 have one episode and 200 have two. The 200 confirmed terminations precede their distinct successor episodes by one day in this scenario. The five projections have no exact duplicate rows or orphan references in the audited joins. Several optional demographics and usage fields are wholly blank. Misata has one native subscription per account, and 1,044 of 1,200 accounts have invoice coverage.
- **Churn and cohorts.** The reconstruction identified 151 positive and 14,212 negative observations, 895 right-censored, zero pending under the explicit follow-up attestation and 3,403 ineligible due to insufficient history. The first eligible positive was observed on 30 September 2022 and the first authoritative termination occurred on 5 October 2022. The original training period ended before either. The previously scored split reproduced 66, 10 and 19 positive episodes. Differences in episode age and establishment cohorts and exclusions by earlier episode assignment are descriptive evidence. The scored period has already been inspected and requires replacement as an untouched holdout for later model selection.
- **Billing and usage.** Fieldwise recorded 14,273 monthly and 514 annual invoices with £1,566,111.80 in issued amounts. The median usage row has four active users, 30 sessions and 152 events. Usage spans April 2021 to February 2024 under the completed-month rule. UCI contributed 1,067,371 native retail lines, including 243,007 without customer IDs and 34,335 repeated normalised lines. The notebook retains these in source totals and states the filters applied to customer-level summaries.

### 17.1 Final acceptance

**PHASE 04 — DATA UNDERSTANDING & EXPLORATORY DATA ANALYSIS: ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS.**

The Project Owner authorised acceptance subject to verification. AC-01 through AC-07 passed. All three notebook sources passed schema validation and fresh Python 3.12.3 kernel execution, producing seven figures across 13 code cells. Local raw inputs were verified byte-for-byte before and after execution. The 27 targeted tests and 1,058 collected regression tests passed, with no failures or skips. The existing Batch 09 model-fitting test was excluded from collection. Ruff lint and formatting, dependency consistency and Git whitespace checks passed. The accepted architecture, generator, contract and pipeline interfaces were preserved.

Fieldwise distributions and the one-day successor interval are properties of the fictional scenario. Positive support is small and temporally concentrated. Recent usage coverage remains incomplete. Misata and UCI retain their native grains and interpretation boundaries. The earlier scored partition is development evidence and requires replacement as an untouched holdout. A clean notebook environment was used to avoid an incompatible optional PySpark backend in the shared environment.

### 17.2 Phase 05 handoff

- Use the canonical subscription episode at an explicit observation time as the prediction grain. Preserve account identifiers for grouping and keep account-level aggregates distinct from episode metrics. Scope historical contributions and prevent information from successor episodes entering earlier observations.
- Use the existing 90-day history and 30-day outcome horizon as experimental references. Define eligible windows and event, effective and availability cut-offs explicitly. Separate observed zero, missing expected usage, structurally unavailable periods and evidence that arrived after observation.
- Evaluate episode tenure, billing cadence, eligible invoice history and completed usage history with explicit denominators. Keep invoice amounts and monthly-normalised recurring amounts distinct. Exclude future status, payment, termination and availability evidence from features.
- Investigate single-plan and deterministic reactivation artefacts before treating apparent relationships as transferable. In later evaluation, use forward maturity and group isolation, check cohort and covariate shifts, and reserve a fresh untouched holdout with adequate independent positive support.

The Project Owner subsequently authorised Phase 05 implementation. See §18.

## 18. Phase 05 point-in-time feature engineering

The implementation is for the fictional Fieldwise development reference only. It applies ADR-009/010 and CGQ-013 and preserves Customer Data Contract v1.1 and the outcome rules of `fieldwise-subscription-churn` v1. The 90-day feature window and 30-day outcome horizon are experimental parameters supplied through `ChurnExperiment`. They confer no production policy approval. The standalone Charter, complete roadmap copy and original FDB-001 evidence remain unavailable for independent traceability. Phase 06 is recorded in §19.

### 18.1 Observation, source and feature contract

The key is the canonical `subscription_id` and the UTC observation timestamp. `build_feature_matrix` requires a currently verified development export and partitions evidence by canonical episode and account before computing features. Prediction eligibility is recorded for every candidate before outcome adjudication. The as-known risk set checks canonical identity, explicit exclusions, known establishment and activation, sufficient history, a usable historical snapshot and absence of an already-known effective termination. Caller-supplied exclusions must reflect the prediction-time policy. Pending and right-censored outcomes may have valid predictor rows. A late record can retrospectively make an observation ineligible for the experimental target while leaving its as-known prediction eligibility intact. The optional outcome assembler preserves existing classifications and flags retrospective training eligibility only when an eligible predictor row also has a resolved binary outcome.

The source projections are verified using the existing five-file contract checksums and development gates. Their internal lifecycle, snapshot, usage and billing evidence is needed for point-in-time use. Customer and subscription identity establish attribution, while final subscription state is excluded from predictor construction. Misata and UCI remain separate analytical populations.

`FEATURE_SPECS` in [feature_matrix.py](../../src/nowa_customer_intelligence/data/synthetic/feature_matrix.py) is the ordered, versioned registry. It defines individual names, types, nullability and calculations. The following rules apply to each feature in its group. Integer counts are non-negative except signed changes. Numerical values must be finite, the coverage ratio must lie in [0, 1], and plan, cadence and monthly amount must reconcile to the fictional catalogue.

| Group and feature names | Source fields and calculation | Window, availability and missingness |
|---|---|---|
| Episode — `episode_age_days` | Internal lifecycle establishment `effective_at`. Whole UTC days since establishment, integer. | Lifetime through observation. Establishment occurrence, effective time and availability must all be at or before observation. Missing or conflicting establishment fails extraction. Final status, end dates and own termination timing are excluded from predictors. |
| Customer history — `prior_completed_episodes` | Canonical same-account episodes and authoritative establishment and termination facts. Integer count of distinct prior episodes established before and completed no later than current establishment. | Available facts through observation. Both facts must have occurred, become effective and been available by observation. Zero means no qualifying known predecessor. A later successor cannot contribute. This feature can expose the fictional reactivation pattern. |
| Commercial — `plan_id`, `billing_frequency`, `monthly_recurring_gbp` | Latest usable subscription snapshot plan, cadence and monthly-normalised recurring revenue. Two native strings and exact Decimal GBP. | Latest snapshot with observation, occurrence, effective and availability times at or before observation. The existing historical eligibility check requires usable commercial and activation evidence. Current-state master fields and retrospective status are excluded. |
| Billing — `issued_invoice_count`, `issued_amount_gbp`, `mean_invoice_gbp`, `days_since_last_invoice` | Episode-linked invoice ID, issue date and amount. Count, Decimal sum, Decimal mean rounded to pennies and whole UTC days since latest known issue date. | Issue boundary within the inclusive history interval. Require a matching internal billing fact with occurrence, effective and availability times at or before observation and occurrence at or after issue. For these immutable fictional charges, that fact conservatively establishes availability. No issue-date-only fallback or payment-status predictor. Zero counts available invoices only. Monetary and recency fields are null when none qualify. No completeness claim is made about an absent charge. |
| Usage coverage — `expected_usage_months`, `observed_usage_months`, `unobserved_usage_months`, `usage_coverage_ratio`, `active_user_months` | Usage label, inclusive period bounds, `available_at` and `active_users`. Counts of expected whole months, available rows, their gap, available divided by expected, and available rows with a known active-user value. | Only whole UTC calendar months fully contained in the history interval and starting on or after known activation. Require explicit availability from month end through observation. Partial or structural periods are outside the denominator. Missing and not-yet-available rows produce the same as-known gap. The ratio is null when no months are expected. |
| Usage levels — `zero_active_user_months`, `latest_active_users`, `mean_active_users`, `max_active_users`, `latest_sessions`, `mean_sessions`, `latest_events`, `mean_events` | Available rows' `active_users`, `sessions_count` and `events_count`. Count literal observed zero active-user months. Latest values refer to the most recent accepted row. Means use known values and the maximum uses known active-user values. | Same monthly availability gate. Counts are integers, means are floats. Missing latest cells and aggregates with no known value remain null. A recorded zero remains a valid observation. Do not infer activity for absent months. |
| Usage trends — `active_users_change`, `sessions_change`, `events_change` | Latest value minus preceding value for each of the three usage measures, signed integers. | Same monthly availability gate. Require the latest two available rows to be consecutive with known values for the corresponding measure. Otherwise return null. No ratios or imputation. |

Date-only invoice issues use the existing fictional UTC issue-day convention, with the additional availability guard above. Billing amounts measure issued charges. The snapshot amount is monthly-normalised. Neither represents recognised revenue or cash collection. Client invoice-issue availability, account-level aggregates of billing/activity, cancellation notice, future renewal, outcome fields, calendar shortcuts and unavailable usage volume are outside the feature registry. Complete historical coverage, plan diversity, independent event support and a fresh evaluation design remain limitations for later authorised work.

### 18.2 Local replay and integrity

Run the command from the repository root in the project Python 3.12 environment:

```bash
PYTHONPATH=src python -m nowa_customer_intelligence.data.synthetic.feature_exports \
  --output data/processed/phase05-fieldwise-final \
  --registry data/interim/phase05-fieldwise.sqlite
```

Use a new output directory and the same local Registry path for a byte-replay check. Add `--inference-only` to omit outcome adjudication and the outcome file. The Python interface supports the equivalent `include_outcomes=False` setting. A fresh Registry allocates different canonical UUIDs. The temporary input directory is cleaned at run exit. The Registry and all bundles remain Git-ignored.

| File | Contents |
|---|---|
| `observations.jsonl` | Identity, UTC observation timestamp, account grouping and latest used evidence timestamp. Ordered by observation timestamp and canonical ID. |
| `predictors.jsonl` | Only the 25 ordered features, aligned by row position with observations. Decimal GBP values are exact strings in JSON and unknown values are JSON nulls. |
| `prediction_eligibility.jsonl` | All candidate keys and their as-known exclusion reason or null for eligible observations. |
| `outcomes.jsonl` | Optional ledger of all candidate keys, horizon, ascertainment, classification and retrospective training eligibility. Unresolved and retrospectively ineligible states have null binary targets. Join by key when needed. |
| `manifest.json` | Bundle version 2, predictor spec version, scenario and experiment parameters, attestation, input inventory and hashes, internal evidence hash, coverage, distribution and missingness checks, and output byte lengths and SHA-256. |

### 18.3 Reference verification

The reference reproduced 1,000 customers, 1,200 episodes, 14,787 invoices, 16,547 monthly usage records and 18,661 snapshots. The snapshot population yields 18,661 candidate observations, of which 15,258 have predictor rows. The 3,403 ineligible observations are retained in the separate outcome ledger. Labels remain 151 positive and 14,212 negative, with 895 right-censored and zero pending under the explicit reference attestation.

The 25-feature bundle has zero duplicate keys or invalid values. Invoice amount, mean and recency are each missing in 3,020 rows with no qualifying charge. Each trend is missing in 12,836 rows because these rows have one available month out of two expected. The remaining 2,422 rows have two consecutive available months out of three expected. The reference convention makes the usage row for the month ending at observation unavailable until at least the next day. This explains the one-month gap without treating it as zero activity. All other features are populated in the reference. Coverage ranges from 50% to 66.67%. The usage gap reflects the fictional observation calendar and reporting lag and is not an empirical GB benchmark.

Offline tests exercise future and late invoice and usage evidence, future terminations and successors, exact availability and lookback boundaries, missing versus zero, canonical grouping, label isolation, malformed outputs, deterministic ordering and source immutability. No split or model was created.

### 18.4 Final acceptance

**PHASE 05 — FEATURE ENGINEERING: ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS.**

The final audit found that retrospective ineligibility previously controlled predictor inclusion. The corrected bundle builds the as-known roster first and optionally adds the existing retrospective outcome classifications. An offline case showed that late evidence of termination could change a pending outcome to retrospectively ineligible while leaving the prediction roster and predictor values identical. A termination already known at observation excluded the same episode. The inference-only build reproduced the eligibility, metadata and predictor files of the adjudicated reference build without generating an outcome ledger.

The corrected reference retained 15,258 prediction rows, including all 895 right-censored observations. The only prediction exclusions were 3,403 observations with insufficient history. There were 14,363 eligible rows with a resolved binary label. Reference predictor and observation files matched the previous implementation byte-for-byte, and all prior outcome classifications were preserved. All five new bundle files matched on same-Registry replay, and their recorded input and output checksums were verified.

FE-01 through FE-12 passed for the authorised fictional development scope, subject to documented limitations on contractual diversity, billing availability, usage coverage and replay. The 41 targeted tests and 1,068 regression tests passed without failures or skips. The Batch 09 model-fitting integration test was excluded from collection. Ruff lint and formatting, dependency consistency and Git whitespace checks passed.

The single-plan catalogue, deterministic reactivation schedule, severe class imbalance and high trend missingness limit transfer beyond this scenario. The history and horizon windows are experimental. Byte reproducibility is established with the same Registry and environment. Production evidence-availability policies remain unverified, and a fresh independent holdout is required for future model evaluation. This acceptance covers feature engineering only.

## 19. Phase 06 churn modelling

**PHASE 06 — CHURN MODELLING: ACCEPTED AND COMPLETED WITH DOCUMENTED PREDICTIVE LIMITATIONS.**

The [Phase 06 protocol](../05_ml/phase06_churn_evaluation_protocol.md) defines a
forward, customer-disjoint evaluation using the accepted Phase 05 features and
outcomes. The previously examined Batch 09 test period is excluded from seed-42
development. A single separately seeded Fieldwise reserve was built using an
isolated Registry. The label-only audit retained 4,254 training rows with 55
positive accounts, 717 validation rows with eight positive accounts and 4,806
reserve rows with 19 positive accounts. Validation missed the 10-account
confirmation floor. The reserve remains unscored.

The declared menu includes a prior dummy, two L2 logistic configurations, two
Random Forest depths and two histogram gradient boosting configurations. The
balanced 15-leaf boosting fit ranked first on validation AP (0.01138 versus a
dummy AP of 0.01116). Its ROC-AUC was 0.23272. At the validation F1 threshold it
flagged 703 of 717 rows, finding all eight positives and producing 695 false
alerts. Its in-sample AP was 0.81966. These are exploratory results with weak
ranking evidence and limited positive support.

The two required research notebooks are:

1. [05_churn_baseline_models.ipynb](../../notebooks/03_churn_modelling/05_churn_baseline_models.ipynb)
2. [06_churn_advanced_models.ipynb](../../notebooks/03_churn_modelling/06_churn_advanced_models.ipynb)

Both render the local research artefacts without fitting. See the
[replay instructions](../../notebooks/README.md#phase-06-churn-modelling).

### 19.1 Project Owner final acceptance

**Engineering acceptance granted.** The accepted experimental scope includes the
modelling pipeline, temporal and group-isolation protocol, evaluation and scoring
logic, automated tests and both notebooks. The seven evaluated configurations and
historical selection decision are retained as experimental evidence. The
[scoring integrity audit](../05_ml/phase06_churn_evaluation_protocol.md#scoring-integrity-audit)
reproduced the nominated model's saved validation metrics from its frozen
pipeline. The fixed threshold, target and feature contract were preserved.

Final verification passed 44 targeted tests and 1,091 regression tests with
the historical Batch 09 model-fitting test excluded. Both notebooks rendered
in fresh Python 3.12 kernels with no fitting. Ruff, dependency consistency,
notebook schema checks and Git whitespace checks passed. The retained research
artefacts and source data matched their recorded checksums.

**Predictive and production approval remain withheld.** Severe class imbalance
left eight positive validation accounts against the required ten. Validation
AP was weak, supervised candidates had ROC-AUC below 0.50, and the nominated
candidate alerted on almost the entire validation population. Its large
training–validation AP gap and the potential influence of generator timing and
behaviour rules warrant caution. The cause of poor ranking remains unresolved.
The evidence does not establish satisfactory ranking, useful operational
prioritisation, stable calibration or independent generalisation. The seed-2027
reserve remains unscored. No real customer validation has been performed. Future
deployment requires additional evidence and separate approval.

## 20. Phase 07 customer lifetime value modelling

**PHASE 07 — CLV MODELLING: ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS.**

The [economic definition and evaluation record](../05_ml/phase07_clv_economic_definition_and_validation.md)
records the approved CLV-PO-001 through CLV-PO-004 decisions. The fictional historical analysis uses Decimal GBP issuance with
canonical invoice-to-episode-to-account attribution and explicit evidence
availability. Active and completed episodes contribute known issuance.
Reactivation preserves both episode identities and the owning account. The
active snapshot's monthly-normalised amount is a separate contractual measure.

The accepted seed-42 scenario reconstructed 1,000 accounts, 1,200 episodes,
18,661 snapshots and 14,787 invoices for April 2021 through March 2024.
Issued amount totals £1,566,111.80, of which £1,127,567.00 is monthly and
£438,544.80 is annual. The 1,000 active episodes at extraction have usable
snapshot amounts totalling £77,056.60 per month. Future outcomes require an
approved economic definition and completeness rules. Holdout data and churn
probabilities from Phase 06 are outside the CLV analysis.

[07_clv_historical_value_and_baselines.ipynb](../../notebooks/04_clv_modelling/07_clv_historical_value_and_baselines.ipynb)
presents the verified descriptive work and calendar headroom. [08_clv_predictive_models_and_validation.ipynb](../../notebooks/04_clv_modelling/08_clv_predictive_models_and_validation.ipynb)
records the approved six-month gross billed-value proxy, fixed research design
and financial evaluation.

The historical notebook ran in a fresh Python 3.12 kernel with 17 code cells
and eight figures. Its month-end screen left 33, 30 and 24 of 36 observation
landmarks with calendar room for illustrative 3-, 6- and 12-month horizons.
The screen establishes neither complete follow-up nor label maturity.
The regression passed 1,099 tests with the historical Batch 09 fitting test
excluded. Ruff, dependency consistency, notebook schema and Git whitespace
checks passed. The retained source and Phase 06 artefact checksums matched.

### 20.1 Approved predictive experiment

CLV-PO-001 approves the canonical account target `future_6m_issued_gbp`.
CLV-PO-002 includes legitimate episode invoices, including reactivations.
CLV-PO-003 separates mature zero from missing or incomplete follow-up.
CLV-PO-004 approves temporal and group isolation, validation MAE and a separate
CLV reserve. Label-only support checks passed before fitting.

The training, validation and reserve populations included 303, 180 and
802 distinct accounts respectively. Histogram Gradient Boosting led validation
MAE at £58.27 versus the training-median baseline of £112.96. The separately
generated seed-731 reserve was scored after freezing the candidate and returned
MAE £51.57. Synthetic schedule effects and positive forecast bias remain relevant
limitations. Real customer value, cash and profit remain outside this evidence.


Initial predictive verification passed 41 targeted tests and 1,108 regression
tests with the historical Batch 09 model-fitting test excluded. Notebook 07
rendered 18 code cells and nine figures. Notebook 08 rendered 11 code cells and
six figures. Both executed in fresh Python 3.12 kernels. The retained source
data, Registries and Phase 06 artefacts matched their recorded checksums.

### 20.2 Project Owner final acceptance

The owner accepted the engineering implementation and synthetic predictive
evidence within the approved experimental scope. CLV-PO-001 through CLV-PO-004
remain in force. The target is six-calendar-month gross issued GBP at canonical
customer grain. It is a billed-value proxy. Cash collection, recognised revenue,
margin, discounting and lifetime extrapolation remain outside scope.
Commercial financial decision-making and production deployment remain unapproved.

Final verification passed 41 targeted checks and 1,108 regression tests with
the historical Batch 09 model-fitting test excluded. Fresh Python 3.12 kernels
rendered Notebook 07 with 25 code cells and 18 figures and Notebook 08 with
27 code cells and 29 figures. These are the comprehensive revisions. Both
source notebooks have cleared outputs. Retained datasets, Registries, models
and research reports matched their checksums. The seed-2027 Phase 06 holdout
remains unscored.

**Predictive limitations.** Development and reserve populations are fictional and
share the same generation mechanism. The seed-731 reserve has one observation date.
Only the frozen nominee was scored, so no independent baseline comparison exists.
Training and validation errors differ substantially. Annual-cadence validation MAE
(£120.72) exceeds monthly MAE (£32.13). Mixed cadence has eight rows from four
accounts. Lower realised-value bands tend to be overforecast and higher bands
underforecast. Repeat observations contribute to the 355 validation rows from
180 accounts. Account-bootstrap intervals condition on the fitted model and omit
full model-selection uncertainty. Real-customer generalisation and commercial
utility remain unverified, and no approved operational error tolerance establishes
commercial suitability.

**Deferred engineering.** The contractual billing baseline requires verified
future retention and renewal assumptions. Account-level product usage features
require a valid temporal aggregation policy. Neither is part of the completed
implementation.

| Criterion | Acceptance result |
|---|---|
| CLV-01 | Passed. Approved six-month billed-value target implemented. |
| CLV-02 | Passed. Canonical account roll-up preserves episodes and invoice lineage. |
| CLV-03 | Passed with documented limitations. Verified fictional issuance within the observed source window. |
| CLV-04 | Passed. Decimal GBP aggregation and explicit monetary semantics. |
| CLV-05 | Passed. Point-in-time features and separate future evidence. |
| CLV-06 | Passed. Mature zero, unknown, incomplete and censored evidence remain distinct. |
| CLV-07 | Passed. Historical amounts reconcile at invoice, episode and customer grain. |
| CLV-08 | Passed with documented limitations. Training-median baseline evaluated. Contractual baseline deferred. |
| CLV-09 | Passed. Three fixed regression candidates evaluated on identical validation rows. |
| CLV-10 | Passed. Forward maturity, account isolation and a separate synthetic reserve. |
| CLV-11 | Passed. GBP error metrics, signed bias, cohort diagnostics and conditional uncertainty reported. |
| CLV-12 | Passed. Historical and baseline notebook verified. |
| CLV-13 | Passed. Predictive models and validation notebook verified. |
| CLV-14 | Passed. Automated and notebook checks verified under NEDS v1.1. |
| CLV-15 | Passed. Approved architecture and phase boundaries preserved. |

## 21. Phase 08 customer segmentation

**PHASE 08 — CUSTOMER SEGMENTATION: ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS AND NEGATIVE MODEL NOMINATION.**

The Project Owner approved SEG-PO-001 through SEG-PO-005. The evidence uses
verified fictional Fieldwise Cloud exports and canonical accounts observed at
UTC month end. The standalone Charter and complete approved roadmap were
unavailable in the reviewed references. The sequence follows the owner brief
and approved phase alignment. The experimental scope excludes commercial
assignment, prior reserves and Phase 06 or Phase 07 predictions.
[Approved scope and frozen protocol](../05_ml/phase08_segmentation_scope_and_validation.md).

| Observation | Role | Visible | Complete history and eligible | Short history |
|---|---|---:|---:|---:|
| 31 March 2023 | Fit | 658 | 338 | 320 |
| 31 December 2023 | Temporal candidate validation | 915 | 573 | 342 |
| 31 March 2024 | Subsequent assessment | 1,000 | 658 | 342 |

The primary modelling cohort requires a complete 12-calendar-month window
and source attestation. Traditional RFM uses verified point-in-time gross
issued GBP with exact arithmetic, deterministic tied quantile bands and
frozen development boundaries. The cadence-specific method uses supported
monthly and annual rules. Mixed cadence had only 21 development accounts
against the 30-account floor. At the final date the traditional and
cadence-aware methods assigned 658 and 619 accounts, with 418 exact matches
on the 619 common assignments.

Account usage requires an attributable whole-month record from one active
episode. The one-day synthetic reporting lag leaves zero complete
three-period usage windows at the agreed month ends. The March 2024 audit
reconciled all 3,000 expected account-months. The earlier summary omitted
82 with no known active episode and 78 with partial coverage. The other
statuses were 1,839 observed, 967 awaiting reporting, 34 with multiple
episodes and zero missing or unavailable. Financial and contractual
evidence was unchanged. Three latest complete and available reporting
months remain a deferred investigation subject to separate Project
Owner approval. Older, available periods support descriptive analysis.
FS-03 failed its 80% complete-window gate and was excluded. FS-01 has three
effective financial coordinates, FS-02 has eight financial and contractual
coordinates, and FS-02 without direct cadence has five. The batch preserves
the accepted Phase 05 and Phase 07 registries.

### 21.1 Experiment and limitations

The frozen protocol assessed 45 configurations across K-Means, Ward and
diagonal Gaussian mixtures at 2–6 groups. All completed and all iterative
candidates converged. Development group support rejected 28 candidates.
The other 17 advanced to stability assessment, where three failed the
stability gate. The full set of overlapping rejection counts is in the
approved scope record. No candidate passed every nomination gate. The
financial two-group K-Means fit assigned 258 and 80 accounts, had silhouette
0.745, and median subsample ARI 1.000 in both
stability modes. Its cadence NMI was 0.793 and catalogue-rate NMI 0.822,
both above the 0.65 ceiling. The no-cadence four-group K-Means candidate
had support and stable resampling. Its common-space silhouette was 0.040
at fit and 0.116 in December against the floor of 0.20. Ward has no native
assignment. These results support financial descriptions and a negative
nomination decision.

December was used for frozen candidate comparison. March 2024 has historical
financial-reference migration only because no model was nominated. Of 573
shared traditional assignments, 541 retained their score and 32 changed.
There was no subsequent model transfer. The isolated seed-83108 reserve has
671 eligible accounts among 1,000 visible and remains unscored. Its distinct
fictional client, Registry and source fingerprints are retained outside Git.

Both notebooks are delivered without saved outputs and replay checksum-verified
research reports in fresh kernels.
[Financial and behavioural profiling](../../notebooks/05_customer_segmentation/09_rfm_and_customer_profiling.ipynb),
[clustering and validation](../../notebooks/05_customer_segmentation/10_customer_clustering_and_validation.ipynb).

### 21.2 Engineering assessment

| Criterion | Result | Basis |
|---|---|---|
| SEG-01 | Passed | Five approved owner decisions recorded. |
| SEG-02 | Passed | Unique account-month grain and eligibility reconciled. |
| SEG-03 | Passed | Canonical account, episode and invoice attribution preserved. |
| SEG-04 | Passed | Point-in-time windows, late facts and usage cut-offs verified. |
| SEG-05 | Passed | Exact gross issuance preserved and reconciled. |
| SEG-06 | Passed with documented limitations | All 3,000 expected periods reconciled. FS-03 failed complete-window coverage. |
| SEG-07 | Passed with documented limitations | Frozen traditional and cadence-aware references verified. Mixed cadence has insufficient fitting support. |
| SEG-08 | Passed | Training-only scaler, feature weights and validation applied. |
| SEG-09 | Passed | Fixed candidate grid executed with recorded seeds and parameters. |
| SEG-10 | Passed | Internal metrics, family diagnostics and common-space comparisons recorded. |
| SEG-11 | Passed | Support screened using prespecified absolute and proportional floors. |
| SEG-12 | Passed | Repeated seeds and controlled account subsampling evaluated. |
| SEG-13 | Passed with documented limitations | December candidate transfer and historical RFM changes measured. No nominee for March model transfer. |
| SEG-14 | Passed with documented limitations | Candidate and RFM profiles reconciled. No nominated operational segments. |
| SEG-15 | Passed | Cadence, feature sensitivity, reactivation and catalogue effects quantified. |
| SEG-16 | Passed | Prespecified gates produce a documented negative result. |
| SEG-17 | Passed | Profiling notebook delivered and replayed. |
| SEG-18 | Passed with documented limitations | Clustering notebook and fitted evidence delivered. Nominee-dependent March model transfer and reserve scoring remain unavailable. |
| SEG-19 | Passed | Controlled tests, regression and artefact verification completed. |
| SEG-20 | Passed | Accepted specifications, earlier evidence and phase boundaries preserved. |

The Project Owner's conditional acceptance is now recorded for the engineering
implementation, experimental clustering research and descriptive financial RFM
analysis. The negative nomination result stands. Operational segment
assignment, production deployment and commercial use remain unapproved.
No real-customer validation or commercial effect has been demonstrated.

Final verification passed 72 targeted tests and 1,132 regression tests.
The historical Batch 09 model-fitting integration was excluded. Both
notebooks replayed in fresh Python 3.12 kernels with 20 and 22 figures.
Notebook schema, links, Ruff lint and format, dependency consistency,
whitespace and retained artefact checksums passed. No Phase 08 research model
was refitted, and the Phase 06 and Phase 07 frozen evidence remains intact.

## 22. Phase 09 explainable AI

**PHASE 09 — EXPLAINABLE AI: ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS.**

The Project Owner approved XAI-PO-001 through XAI-PO-005. The Phase 08
checkpoint remains synchronised and its negative model nomination remains
recorded. The Phase 09 work delivers CLV billed-value research, churn model
diagnostics and deterministic RFM interpretation in documentation.
[Scope and validation specification](../05_ml/phase09_explainability_scope_and_validation.md).

The final audit checked both frozen model fingerprints and fitted lineage,
and reconciled the retained evidence for all 717 churn and 355 CLV
development-validation outputs. Churn interventional TreeSHAP passed on
class-1 probability and log odds (98 rows per scale, maximum residuals
2.51e-9 and 4.21e-8). Episode age led the mean absolute probability
attribution at 0.11781. The explained false positive scored 0.9191,
and the eight positive validation accounts and 695 false positives limit
predictive interpretation.

CLV interventional TreeSHAP failed on all 12 signed raw checks, with a
maximum discrepancy of £9.66 and an unresolved cause. Path-dependent
TreeSHAP reconciled on the signed pre-clip scale. The validated method
uses four original-feature blocks, 16 coalitions and the final clipped
six-month gross issued GBP predictor. The £486.65 training-reference
baseline and signed contributions reconstruct all 102 forecasts within
£1.14e-13. Invoice history and cadence led mean absolute attribution
at £112.16. Its matched-account permutation increased row MAE by £138.05
(sample SD £9.06) relative to £58.27 on the same 355 rows from 180
accounts over 30 repetitions. The local cases include a £473.41
forecast against £1,327.20 recorded and a −£3.83 raw estimate clipped to £0.

Identical-background replay showed zero change. The primary 64-account
training references included 61 February 2023 churn rows and 64 June
2022 CLV rows. Four alternate backgrounds and 100 account-bootstrap
draws gave median rank correlations of 0.984 and 0.995 for churn and
1.000 for both CLV diagnostics. Individual contributions shifted by
up to 0.07225 probability or £24.15 across backgrounds. Supported
PDP/ICE points use variable account denominators. None of the four
predeclared interaction grids supported a matched four-corner contrast.

Acceptance covers frozen-model explanation engineering and internal
synthetic research. Operational risk scoring, validated commercial
churn prediction, financial recommendations, causal claims, customer
interventions, revenue-at-risk and production deployment remain outside
scope. Accepted modelling results and protected reserve evidence were
preserved. The final audit passed 87 targeted and 1,147 regression
tests with the historical Batch 09 fitting integration excluded. Both
notebooks rendered in fresh kernels and their repository copies have
cleared outputs and counters.
[Churn notebook](../../notebooks/06_explainable_ai/11_churn_model_explainability.ipynb),
[CLV notebook](../../notebooks/06_explainable_ai/12_clv_model_explainability.ipynb).

### 22.1 Engineering acceptance matrix

| ID | Requirement | Result | Evidence |
|---|---|---|---|
| XAI-01 | Approved scope | Passed | XAI-PO-001 through XAI-PO-005 preserved. |
| XAI-02 | Frozen model provenance | Passed | Model hashes, accepted designs and saved research evidence verified. |
| XAI-03 | Reference populations | Passed | Training-only reference, prior development validation and distinct-account samples checked. |
| XAI-04 | Feature contract and lineage | Passed | Churn 25→40→30 and CLV 17→29 verified against fitted lineage. |
| XAI-05 | Output-scale interpretation | Passed | Class-1 probability, log odds and clipped issued GBP interpreted on their respective scales. |
| XAI-06 | Global explanations | Passed | Mean absolute contributions on 96 distinct validation accounts per model. |
| XAI-07 | Local explanations | Passed | Anonymised cases and additive reconstructions reconciled. |
| XAI-08 | SHAP or justified alternative | Passed with documented limitations | Churn TreeSHAP passed. CLV signed interventional probe failed and the clipped four-block game passed. |
| XAI-09 | Permutation importance or alternative | Passed with documented limitations | CLV matched-account MAE deltas verified. Calendar stayed fixed and churn performance permutation was withheld. |
| XAI-10 | PDP and ICE | Passed with documented limitations | Grids and account support checked. Four matched-contrast grids lacked support. |
| XAI-11 | Additivity and consistency | Passed | Zero failures on all delivered modes at their frozen tolerances. |
| XAI-12 | Stability | Passed with documented limitations | Identical replay, four alternative backgrounds and 100 bootstraps checked. Local changes and temporal concentration documented. |
| XAI-13 | Churn predictive limitations | Passed | Weak ranking, eight positives and 695 false positives remain visible. |
| XAI-14 | CLV financial interpretation | Passed | Issued GBP target, clipping, cadence and error examples verified. |
| XAI-15 | Segmentation and RFM interpretation | Passed | Deterministic RFM and Phase 08 negative nomination preserved. |
| XAI-16 | Correlation and causality | Passed | Within-block relationships, implausible hybrids and support restrictions documented. |
| XAI-17 | Churn explainability notebook | Passed with documented limitations | Fresh-kernel replay and churn diagnostic limits verified. |
| XAI-18 | CLV explainability notebook | Passed with documented limitations | Fresh-kernel replay, grouped attribution and failed raw TreeSHAP configuration documented. |
| XAI-19 | Tests and reproducibility | Passed | Targeted and repository regression tests, fingerprints and notebook replay passed. |
| XAI-20 | Prior phase boundaries | Passed | Accepted checkpoints, frozen outcomes and reserves preserved. |

## 23. Phase 10 API development

**PHASE 10 — API DEVELOPMENT: ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS.**

Gate 01 verified the accepted Phase 09 audit and corrective checkpoint against
live GitHub main. WP-10.1 prepared the local-first, read-only research API
design. The Project Owner approved API-PO-001 through API-PO-005 on
21 November 2026. WP-10.2 records the nine GET contracts, authenticated
loopback boundary, pinned evidence catalogue and reliability requirements.
The Phase 09 acceptance and model-use restrictions remain in force.

FastAPI and Pydantic are the approved technologies for the internal,
read-only Research & Analytics API. Phase 11's Power BI adoption adds no
endpoint or integration requirement to the nine approved GET contracts.
WP-10.2 finalises their specification within API-PO-001 through API-PO-005.

WP-10.3 established the application foundation and was synchronised before
the implementation gates resumed. WP-10.4 through WP-10.10 implemented
and audited the nine approved routes, scoped local access, the pinned
catalogue, audit events, contract tests and the isolated API CI job.
The controlled loopback workload was measured with synthetic fixtures.

The Project Owner formally accepted checkpoint
`8403b4fc44000f2744350d03a09c1052b4391c7e`. Hosted `CI` confirmed
77 API tests and 1,092 safe regression tests passed, completing hosted
verification for API-18.
[GitHub Actions run 45032629816](https://github.com/AnderCruz/Customer-Churn-Prediction-CLV/actions/runs/45032629816).

API-07 retains the separate approval requirement for a populated
retained-evidence release and its independent pin. API-08 retains the
secure reader's supported POSIX filesystem requirement. Production or
commercial deployment, operational scoring, customer-specific predictions,
retained-evidence publication and multi-tenant access remain outside the
accepted scope.
[Phase 10 acceptance and verification](../06_deployment/phase10_api_architecture_and_contracts.md#project-owner-acceptance).

## 24. Phase 11 dashboard development

**PHASE 11 — POWER BI DASHBOARD DEVELOPMENT: IN PROGRESS.**

The Project Owner approved the technology direction and DASH-PO-001 through
DASH-PO-004. The acceptance conditions below define the architecture to
verify during Phase 11.

The Project Owner formally initiated Phase 11 under BI-PO-001–007. WP-11.1
is accepted as the project-definition and business-requirements baseline.
WP-11.2 is accepted for analytical data architecture and contract
specification. The six proposed pages depend on verified Fieldwise Cloud
data, disclosure approval for research fields and successful quality gates.
The WP-11.2 specification records the design checks, owner approvals and
implementation checks separately. Local Windows authoring verification
is required. Dataset implementation, research disclosure and later work
packages require separate approval.
[WP-11.1 decision register](../06_deployment/phase11_power_bi_project_definition.md#project-owner-decisions),
[WP-11.2 analytical data contracts](../06_deployment/phase11_analytical_data_architecture_and_contracts.md).

The Project Owner approved the BI-DR-001–010 dispositions. Historical
architecture and read-only Registry reuse are conditional. Local data
governance and canonical NEDS are approved. The Windows PBIP approval
covered the completed fixture-only proof. Research field and cohort
disclosure and historical export implementation remain deferred.
BI-DR-008 originally deferred WP-11.3 initiation. AGENTS.md
was adopted in governance checkpoint `98b544277e17bf9a9287b25247471aa31c0a2aa6`.
[Owner decision register](../06_deployment/phase11_analytical_data_architecture_and_contracts.md#12-project-owner-decision-register).

BI-DR-011 approves the historical reporting definitions. The single
reconstruction authorised by BI-DR-012 matched all accepted source and
typed-evidence fingerprints, reconciled all historical episode mappings
and verified the financial controls. BI-DR-013 defined the acceptance
boundary. BI-DR-014 accepts the reproduced historical reference.
BI-DR-015 formally accepts WP-11.2. BI-DR-016 authorises the
documentation-only acceptance checkpoint.
[Historical reconstruction evidence](../06_deployment/phase11_analytical_data_architecture_and_contracts.md#13-historical-reference-reconstruction-evidence).

**WP-11.1 — ACCEPTED.**\
**WP-11.2 — ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS.**\
**WP-11.3 — ACCEPTED AND COMPLETED WITH DOCUMENTED IMPLEMENTATION LIMITATIONS.**\
**WP-11.4 — PENDING AUTHORISATION.**

| Project Owner decision | Status | Approved scope |
|---|---|---|
| BI-DR-017 — WP-11.3 Initiation & Scope | **APPROVED** | Authorise conceptual and logical semantic architecture, relationships, date roles, KPI and financial semantics, identity, snapshot and usage coverage, research isolation, security, validation and documentation. Supersede BI-DR-008 for initiation within this design scope only. The Windows fixture proof retains its separate BI-DR-007 authority. Exports, Power Query and model implementation, report authoring and production DAX require separate authority. |

BI-SM-001–006 are Approved. BI-SM-007 is Approved with Conditions for
independently verified, allowlisted metadata within the physical contracts.
BI-SM-008 is Deferred. The research isolation requirements and all 34
research-field and associated cohort restrictions remain in force.
BI-DR-019, Approved with Documented Limitations, accepts the design and
fixture-only PBIP proof. BI-DR-020, Approved, authorises the controlled
three-file documentation checkpoint and standard fast-forward publication.

[WP-11.3.1 semantic model design](../06_deployment/phase11_power_bi_semantic_model_design.md),
[WP-11.3.2 Windows fixture evidence](../06_deployment/phase11_power_bi_semantic_model_design.md#14-windows-technical-proof-and-engine-reconciliation),
[WP-11.3 architectural decision register](../06_deployment/phase11_power_bi_semantic_model_design.md#10-architectural-decision-register),
[Formal WP-11.3 acceptance](../06_deployment/phase11_power_bi_semantic_model_design.md#21-formal-project-owner-acceptance-and-documentation-checkpoint).

BI-DR-006 historical export implementation and BI-DR-003–004 research
field and cohort disclosure remain deferred. The BI-DR-007 fixture-only
proof verified local PBIP save, close, reopen, refresh and semantic
behaviour with fictional fixtures. PBIP is the preferred development
and source-control format. The controlled PBIX fallback remains Not
Tested. Historical bundle integration, production Power Query and DAX,
and report authoring remain gated. BI-DR-018 remains an AWS proposal,
and AWS connectivity and deployment remain unauthorised. BI-CT-09 and
BI-CT-11 remain Not Tested for historical implementation. BI-CT-13 and
BI-CT-16 remain Pending Owner
Approval. Phases 12–14 remain pending.
[Formal WP-11.2 acceptance](../06_deployment/phase11_analytical_data_architecture_and_contracts.md#14-formal-wp-112-acceptance).

| Approved decision | Architectural boundary | Acceptance condition |
|---|---|---|
| DASH-PO-001 — Power BI as the Primary Dashboard Platform | Microsoft Power BI is the primary Phase 11 platform. The Streamlit primary-dashboard choice is superseded. | Active roadmap and architecture references identify Power BI as the approved dashboard technology. |
| DASH-PO-002 — Python as the Analytics and Data Preparation Engine | Python owns data engineering, feature engineering, machine learning, explainable AI and verified dataset preparation. Power Query prepares the inputs within Power BI, the semantic model defines relationships and grain, and DAX expresses analytical measures. | The architecture separates Python analytics and preparation from Power BI semantic and reporting responsibilities. |
| DASH-PO-003 — Verified Analytical Datasets for Power BI Integration | Initial reports may use versioned, verified analytical datasets without FastAPI at runtime. Dataset contracts, refresh procedures and semantic models belong to Phase 11. | The architecture records the dataset boundary and preserves the nine approved Phase 10 GET endpoints. |
| DASH-PO-004 — Synthetic Research and Demonstration Scope | Initial reports use authorised synthetic research and retain all accepted churn, CLV, segmentation and explainability limitations. | Experimental results are explicitly excluded from validated commercial prediction claims. |

| Technology | Approved responsibility |
|---|---|
| Python | Data engineering, feature engineering, machine learning and explainable AI. Prepare the verified analytical datasets used by the dashboard. |
| FastAPI and Pydantic | Phase 10 internal research API and typed contracts. |
| Microsoft Power BI | Primary business intelligence and dashboard platform, replacing Streamlit in the active roadmap. |
| Power Query and DAX | Power Query prepares the dashboard inputs. The Power BI semantic model defines relationships and grain, and DAX expresses reviewed analytical measures. |

The proposed initial Power BI integration uses verified, versioned analytical
datasets prepared in Python. These datasets must carry their provenance,
analytical grain, units, evidence scope and limitations. The dashboard has
no mandatory runtime dependency on FastAPI. Dataset delivery and refresh,
semantic-model details, publishing and access boundaries remain Phase 11
design work. Any future Power BI-specific API integration requires a
separate scope decision.

Phase 11 retains the accepted Phase 01–09 records and scientific limits.
Churn remains diagnostic research, billed value remains the six-month gross
issued GBP proxy, clustering has no operational nominee, and explainability
describes model behaviour. Dashboard technology approval does not release
operational scores, risk bands, revenue-at-risk estimates or recommendations.
Phase 12 retains MLOps, Phase 13 retains Docker and AWS, and Phase 14 retains
testing and documentation.

### 24.1 Historical Streamlit references

The approved Power BI direction supersedes Streamlit as the primary
dashboard choice. Earlier records remain available for traceability.

| Historical reference | Active interpretation |
|---|---|
| [Proposed ADR-007](../03_architecture/architecture_decisions.md#adr-007-streamlit-for-mvp-dashboard) | The proposed Streamlit MVP dashboard is superseded by the Power BI direction. |
| [Baseline approval register and PO-006](documentation_review_and_approval.md#6-product-owner-decisions) | The historical selection stands as an approval record. Its primary dashboard choice is superseded. The earlier statement about core batch scoring does not authorise operational scoring under the current research scope. |
| [System architecture](../03_architecture/system_architecture.md), [deployment and MLOps strategy](../06_deployment/deployment_and_mlops_strategy.md) and [business case](../01_business/business_case.md) | Streamlit diagrams, technology lists and MVP descriptions reflect the earlier direction. Use the active roadmap for the primary dashboard choice. |
| [MVP technical design](../03_architecture/mvp_architecture_and_technical_design.md) and [contract revision readiness assessment](../04_data/contract_revision_readiness_and_decision_decomposition.md) | Historical implementation caution and post-MVP Streamlit references do not govern the approved Phase 11 platform. |
| [Repository README](../../README.md), [dashboard placeholder](../../dashboard/README.md) and [optional dashboard dependency](../../pyproject.toml) | These still refer to Streamlit. They require alignment when Phase 11 work is authorised. The dependency declaration records an existing extra and confers no implementation approval. |
