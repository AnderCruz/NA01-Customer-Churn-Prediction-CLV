# Nowa Customer Intelligence — Repository Agent Instructions

**Organisation:** Nowa Analytics  
**Repository:** `AnderCruz/Customer-Churn-Prediction-CLV`  
**Mandatory standard:** Nowa Analytics Engineering & Development Standard (NEDS) v1.1  
**Purpose:** Persistent operating instructions for Codex and other repository-aware engineering agents.

> This file defines **how to work**, not a second project specification, acceptance register, or historical transcript. Follow the latest verified and formally approved project records. Do not use this file as proof that an activity has been executed or accepted.

## 1. Mission and governing boundaries

Build an auditable, reproducible customer-intelligence research platform for a **fictional UK B2B SaaS business, Fieldwise Cloud**, using authorised synthetic data. The project covers data engineering, churn research, six-month issued-invoice-value research, descriptive RFM, explainability, an internal Research & Analytics API, and locally developed Power BI reporting.

Current approved technology direction:

- **Python 3.12**: data contracts, ingestion, synthetic data, feature engineering, ML, XAI, testing and verified BI dataset preparation.
- **FastAPI and Pydantic v2**: the accepted internal, read-only Research & Analytics API.
- **Microsoft Power BI Desktop on Windows**: primary BI reports; Power Query, semantic model and DAX. Prefer PBIP for source control only after real Windows save/reopen/refresh verification; PBIX is a controlled fallback.
- **Linux/WSL2**: existing Python development and the supported POSIX evidence-reader environment.

Power BI **does not require FastAPI at report-refresh time**. Do not introduce PostgreSQL, Redis, Celery, AWS, Docker deployment, public hosting, operational inference, or other infrastructure merely to complete a task. Later roadmap phases do not constitute implementation permission.

## 2. Where to find authoritative context

Read **only the sources relevant to the task**, plus any dependencies or accepted decisions they explicitly reference. Do not load the whole repository for a minor edit.

| Need | Source in this repository |
| --- | --- |
| Canonical NEDS v1.1 | `docs/standards/NA_Engineering_Development_Standard_NEDS_v1.1.md` |
| Approved **14-phase sequence**, phase status, current work package and newer decisions | `docs/07_project_management/implementation_plan_and_roadmap.md` |
| Historical PO decisions and approval trail | `docs/07_project_management/documentation_review_and_approval.md` |
| Business context and use cases | `docs/01_business/business_objectives_and_scope.md`; `docs/01_business/business_case.md` |
| Functional/non-functional requirements and outstanding commercial capabilities | `docs/02_requirements/functional_requirements.md`; `docs/02_requirements/non_functional_requirements.md`; `docs/02_requirements/acceptance_criteria.md` |
| Architecture and ADRs, including superseded alternatives | `docs/03_architecture/architecture_decisions.md`; relevant files in `docs/03_architecture/` |
| Data contract and entity/temporal semantics | `docs/04_data/customer_data_contract.md`; `docs/04_data/subscription_episode_lifecycle_decision_specification.md` |
| Synthetic source model and provenance | `docs/04_data/synthetic_business_model_specification.md`; relevant files in `docs/04_data/` |
| Churn research restrictions and evaluation | `docs/05_ml/phase06_churn_evaluation_protocol.md` |
| CLV financial target and evaluation | `docs/05_ml/phase07_clv_economic_definition_and_validation.md` |
| RFM and clustering decision | `docs/05_ml/phase08_segmentation_scope_and_validation.md` |
| XAI methodologies and limitations | `docs/05_ml/phase09_explainability_scope_and_validation.md` |
| Accepted API contracts, release rules and acceptance | `docs/06_deployment/phase10_api_architecture_and_contracts.md` |
| Phase 11 planning baseline and owner decisions | `docs/06_deployment/phase11_power_bi_project_definition.md`; `docs/06_deployment/phase11_analytical_data_architecture_and_contracts.md` |
| Implementation/dependency conventions | `pyproject.toml`; `.github/workflows/ci.yml`; relevant source and tests |

**NEDS authority:** BI-DR-009 designates the canonical v1.1 copy above. Preserve its approved text and report any missing or mismatched mandatory reference before proceeding through the affected gate.

**Source precedence:** NEDS and explicit formal Project Owner authorisation govern; use the most recent approved PO/ADR decisions and phase acceptance records to resolve historic proposals. The live roadmap identifies current progress. Code and tests demonstrate *implementation*, not owner approval. Escalate unresolved contradictions; never silently reinterpret an older draft as a current requirement.

**Known documentation drift:** The root `README.md`, `dashboard/README.md`, the optional `dashboard` extra in `pyproject.toml`, and older ADR/architecture material still mention Streamlit or an earlier phase/MVP. These are **historical or stale descriptions**, not authorisation to replace Power BI, expose scoring, or declare production readiness. Preserve the historical record; propose controlled updates to current-facing documents when in scope.

## 3. Phase and decision protocol

- The **approved 14-phase roadmap** is the only valid phase sequence; historical shorter or renumbered drafts are not authoritative.
- At the start of a substantial task, identify the phase, work package, source specification, applicable acceptance criteria, accepted dependencies and any latest explicit owner decisions.
- The approved **DASH-PO-001–004** and subsequent **BI-PO-001–007** decisions establish the Power BI direction and initial Phase 11 boundaries. Their most recent owner approvals may not yet appear in the remote roadmap: verify the latest explicit instruction and available local approval records before recording phase status. Do not infer approval from an untracked file or silently discard a later authorised decision.
- Previously accepted phases do not become unaccepted simply because a later phase is being developed.
- Distinguish `proposed`, `approved`, `implemented`, `tested`, `validated`, `accepted`, `deferred`, `blocked` and `production ready`. Never interchange them.
- Plan and implement the **smallest authorised increment**. Each new work package requires separate Project Owner authorisation unless a previously approved instruction explicitly authorises a defined sequence of work packages. Apply each mandatory Quality Gate separately. Stop at a failed gate or an owner-controlled decision.
- Do not enter a new phase, publish data, deploy, commit, push, create a tag, amend or rewrite Git history without explicit authorisation appropriate to the operation.

## 4. Non-negotiable research integrity

Treat accepted development evidence and frozen artefacts as read-only. Access only approved development artefacts needed for the task. Protected reserves are outside routine inspection, hashing, testing and replay. Reserve access requires separate, explicit Project Owner authorisation for the specific operation.

- **Churn / Phase 06:** 30-day **subscription-episode** contractual churn with documented predictive limitations. The frozen classifier is diagnostic research. Operational scoring, risk bands, targeting and revenue-at-risk are outside its approved scope. The independent **seed-2027 holdout remains unscored**.
- **CLV / Phase 07:** account-level `future_6m_issued_gbp` = **gross GBP invoices issued over the next six calendar months**, using the accepted horizon and eligibility rules. It is **not** cash collected, recognised revenue, margin, profit, discounted lifetime value or total customer lifetime value. The independent **seed-731 reserve was scored once and is closed**; never rerun or tune using it.
- **Segmentation / Phase 08:** historical descriptive RFM is allowed within its approved scope; the research produced a **negative operational model nomination**. No operational clusters, segment assignments or interventions. The independent **seed-83108 reserve remains unscored**.
- **Explainability / Phase 09:** preserve the separate churn probability and log-odds scales and the accepted **four-block grouped Shapley** explanation of the **clipped CLV output in GBP**. Raw interventional CLV TreeSHAP failed reconciliation. Raw path-dependent CLV TreeSHAP reconciled on the pre-clip scale as compatibility evidence only. Attributions are background-dependent and non-causal. Customer-level explanation publication remains outside scope.
- Never retrain frozen models, reopen protected reserve data, rescore holdouts, replay accepted research notebooks or regenerate results just to populate an API or dashboard. Never run a broad test command without checking whether it triggers those activities.
- Preserve auditable notebook Git blobs, scientific fingerprints, partitions, frozen targets and report provenance. **Do not auto-fix notebook outputs**; report unexpected changes before any restoration.

## 5. Data and analytical reporting boundaries

- Canonical **account/customer** and **subscription episode** are different grains; a terminated-and-reactivated episode retains historical identity and gets a new canonical episode ID. Invoices, snapshots and monthly usage each have their own temporal and attribution rules. Inspect the Customer Data Contract and synthetic lifecycle specification before joining them.
- Synthetic Fieldwise Cloud is the initial approved Power BI scenario. Misata, UCI and other external populations are **not** part of its first release.
- No KPI without an approved definition, source, grain, unit, date semantics, filter behaviour and independent reconciliation. Prevent duplicate invoice sums from fact-to-fact joins and mistaken counting of episodes as accounts.
- Preserve exact monetary and UTC/calendar semantics. Independently reconcile Power BI DAX results against validated Python reference calculations.
- Research aggregates require **field-level disclosure approval** before export/report exposure. Do not equate permitted descriptive synthetic analysis with approval to disclose every retained experiment or individual prediction.
- Initial Power BI work is local-only. No Power BI Service publication, public sharing, live customer connection or cloud refresh without a separate decision. Do not claim PBIP/PBIX works before actual supported Windows Desktop save, reopen and refresh tests.

## 6. Phase 10 API boundary (accepted, not a general scoring service)

- The accepted surface comprises **exactly nine read-only GET routes**: `/health/live`, `/health/ready`, and seven `/v1/research/*` routes defined in the Phase 10 specification.
- Research routes require effective authorisation for a fixed fictional audience and `research:read` scope. Only trusted in-process use or explicitly configured **authenticated loopback** is approved; no public interface or multi-tenancy.
- Research responses come from an allowlisted, immutable, checksum-verified evidence catalogue; missing or unapproved evidence fails closed (`503` for readiness/authorised research requests, while liveness remains independent).
- **The Phase 10 code acceptance is not approval to publish retained evidence.** A populated release and its independently trusted manifest digest require separate owner authorisation. Never use development fixtures as an implicit published release.
- The secure evidence reader requires supported **POSIX** directory-relative/no-follow filesystem operations. Do not introduce an unsafe portability fallback.
- Preserve typed Pydantic contracts, sanitised error handling, audit redaction and no runtime model fitting, inference or SHAP calculations. Do not expand the nine-route contract without approval.

## 7. Working procedure

For an authorised work package:

1. **Discover:** check the current branch and `HEAD`, inspect `git status --short --untracked-files=all` and `git diff --cached --name-status`, and identify existing user changes before editing. Verify the remote baseline when the task requires it.
2. **Orient:** read the relevant roadmap/phase/contract sections and current PO decisions; inspect applicable source and tests. Do not read every phase document by default.
3. **Plan:** state the objective, boundaries, dependencies, deliverables, tests and Quality Gate. Request an owner decision only for genuine missing approvals; do not invent one.
4. **Implement:** make small, coherent changes; reuse project conventions. Avoid speculative abstractions, new tools, dependency churn and unapproved infrastructure.
5. **Verify:** run targeted deterministic tests, quality checks and appropriate **safe** regressions. Capture commands, exit status, actual pass/fail/skip counts and meaningful limitations. Do not claim a CI run succeeded unless its actual logs were checked.
6. **Reconcile:** compare implementation with approved requirements, data contracts, scientific limitations, accepted artefacts and Git diff. Leave unrelated files untouched.
7. **Report:** list exact files, checks actually executed, acceptance criterion results, blockers, excluded tests, Git status and next owner decision. Never mark a phase owner-accepted on your own.

### Existing tools and safe test entry points

- Python version: `>=3.12,<3.13`; inspect `pyproject.toml` for exact extras and dependency ranges.
- Lint: `ruff check .`; format verification: `ruff format --check .`; type checks: use an appropriately targeted `mypy` invocation.
- API tests in a properly provisioned isolated environment: `python -m pytest -q -W error tests/unit/api tests/integration/test_api_*.py`.
- Safe regression selection is **defined in** `.github/workflows/ci.yml` under `quality-and-tests`: reproduce or adapt its explicit exclusion list. **Do not blindly run `pytest` over the entire repository.** Never run historical training, scoring or notebook-replay collections without owner approval.
- Use `python -m pip check` after dependency changes, where applicable.
- Before any allowed commit, inspect `git diff --cached --name-status`, `git diff --cached --check`, branch, parent history and the exact authorised path list. GitHub Actions success must be proven by the exact commit/run, not assumed from local tests.

## 8. Security, review and communication

- No credentials, private keys, customer records, personal data, environment dumps or protected research data in Git, logs, reports or prompts. Prefer least privilege, allowlists, bounded inputs and fail-closed errors.
- Follow NEDS v1.1 and actual repository code style; write code comments, identifiers, commit messages and technical documentation in **British English**. User-facing summaries may use the user's language when requested.
- Prefer explicit, reviewable diffs and evidence over long self-congratulatory summaries. For significant decisions, provide alternatives, trade-offs and a recommendation; never automatically agree with a flawed assumption.
- Do not report proposed features as implemented, model explanations as causal, synthetic results as market evidence, or research API benchmark numbers as scoring SLAs.
- If instructions conflict or a mandatory source/control is unavailable, explain the conflict and stop at the relevant gate. Never bypass safety, research, release or Git controls to complete a task.

## 9. Maintenance of this file

Keep `AGENTS.md` **durable and compact**. Do not paste whole phase plans, output logs, notebooks, metrics tables or evolving work-package statuses here. Refer to their authoritative sources instead. Update this file only for lasting workflow or project-boundary changes, via a controlled review. If a new subdirectory has genuinely distinct rules, a scoped nested `AGENTS.md` may be justified; avoid duplicate global instructions.
