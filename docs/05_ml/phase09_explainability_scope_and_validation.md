# Phase 09 explainability scope and validation

**PHASE 09 — EXPLAINABLE AI: ACCEPTED AND COMPLETED WITH DOCUMENTED LIMITATIONS.**

## Authority and research purpose

Phase 09 explains the behaviour of the frozen Phase 06 churn classifier and
Phase 07 billed-value regressor. It investigates global reliance, local
contributions, interactions, sensitivity, consistency, stability and failure
patterns. Evidence of mathematical fidelity, predictive performance, financial
meaning and commercial actionability must be reported separately. The Project
Owner approved XAI-PO-001 through XAI-PO-005 and authorised bounded research
on the frozen models. Technical choices and observed limits are recorded below.

BO-05 calls for understandable associations with model outputs. FR-032
requests global importance, FR-033 requests supported local explanations,
and FR-034 limits interpretation to model associations. AC-012 calls for
reproducible global and supported local explanations. FR-021–024 govern the
financial target and its assumptions. ADR-009/010 distinguish canonical
contractual episodes from accounts. The product requirements FR-029–031 and
AC-011 for revenue exposure are separate from this initial XAI scope.
[Business objectives](../01_business/business_objectives_and_scope.md),
[functional requirements](../02_requirements/functional_requirements.md),
[acceptance criteria](../02_requirements/acceptance_criteria.md),
[Customer Data Contract v1.1](../04_data/customer_data_contract.md),
[ADR-009](../03_architecture/architecture_decisions.md#adr-009-subscription-level-churn-prediction),
[ADR-010](../03_architecture/adr_episode_identity_and_identifier_management.md).

Reviewed NEDS v1.1, the repository phase alignment, the Phase 05 point-in-time
specification, the accepted Phase 06 and 07 protocols and Phase 08 acceptance
record, the modelling strategy, notebooks, estimators, local saved evidence
and the relevant test suites. The standalone Charter and complete approved
14-phase roadmap were unavailable in the reviewed project references. The
owner brief and recorded phase alignment establish the current sequencing. The
shorter historical planning table and its risk proposals remain historical.
[Implementation roadmap](../07_project_management/implementation_plan_and_roadmap.md),
[modelling strategy](modelling_and_evaluation_strategy.md),
[Phase 06 protocol](phase06_churn_evaluation_protocol.md),
[Phase 07 economic definition](phase07_clv_economic_definition_and_validation.md),
[Phase 08 acceptance](../07_project_management/implementation_plan_and_roadmap.md#212-engineering-assessment).

## Verified frozen model inventory

The audit matched the local frozen records to their saved designs and
checksum-verified reports before loading the two trusted local Joblib binaries.
Only the development seed 42 was used. No protected reserve data files were opened. Accepted scores below come from the retained reports.

| Evidence | Phase 06 churn | Phase 07 billed value |
|---|---|---|
| Model and protocol | `HistGradientBoostingClassifier`, “Gradient Boosting 15 leaves balanced”, `nci-phase06-v1` | `HistGradientBoostingRegressor`, “Histogram Gradient Boosting”, `fieldwise-clv-v1` |
| Model SHA-256 | `16d7a588ec36dc4b22beb20b56f98903af68d4453563921985ba063a024a8cd1` | `250f4d860a662f69f95e2577cd890dc4f86d75c33771bc8dc0ed04aa4398afc7` |
| Entity and horizon | Canonical episode at observation, confirmed contractual churn within the experimental 30-day horizon | Canonical account at observation, `future_6m_issued_gbp`, gross invoices issued during the next six calendar months |
| Ordered raw registry and fitted width | Phase 05 `fieldwise-episode-features-v1`, 25 inputs → 40 transformed → 30 retained | Phase 07 `FEATURES` in `fieldwise-clv-v1`, 17 inputs → 29 transformed |
| Pipeline | `preprocessing` ColumnTransformer → `constant_filter` VarianceThreshold → `model` classifier | ColumnTransformer → regressor. The research scoring wrapper clips negative predictions to zero after the fitted pipeline. |
| Numerical treatment | 23 raw numerical fields, fitted train median imputation with empty columns retained, plus a separate indicator for each of 14 nullable raw fields before filtering. The nominee uses no scaler. | 14 numerical fields, fitted train median imputation with empty columns retained and indicators enabled, then StandardScaler. The frozen imputer learned no missing indicators. |
| Categorical treatment | Dense one-hot: `plan_id=launch` and `billing_frequency=annual/monthly`; unknown categories are ignored. The constant filter removed the launch coordinate. | Dense one-hot: `billing_evidence=issued_evidence`, `cadence=annual/monthly`, and months `01`–`12`; unknown categories are ignored. There is no constant filter. |
| Output | `classes_=[0, 1]`. Select class label `1` explicitly from `predict_proba`. The scalar decision function is its log-odds margin. Research alert threshold **0.003965284793899528**, inclusive. | Identity target scale with squared-error fitting. The signed pre-clip estimate uses issued GBP. The accepted wrapper returns non-negative gross issued GBP. No log or inverse target transformation. |
| Fitting cohort | 4,254 eligible observations, 397 distinct accounts and 55 positive accounts, June 2021 to February 2023 | 2,455 observations, 303 distinct accounts, June 2021 to June 2022 |
| Validation cohort | 717 observations, 205 accounts, 8 positives in 8 accounts, April to July 2023 | 355 observations, 180 accounts, 42 mature zero outcomes, January and February 2023 |
| Saved validation evidence | Candidate metrics, PR/ROC, calibration, intervals and cohort diagnostics. AP **0.0113798009**, ROC-AUC **0.2327221439**, Brier **0.0427329213**. At the retained threshold, TN **14**, FP **695**, FN **0**, TP **8**. | 355 stored row-level validation predictions and summaries. MAE **£58.2657**, RMSE **£152.2617**, median AE **£10.0335**, signed bias **+£8.1558**, R² **0.54360**. Training-median validation MAE **£112.9589**. |

The churn filter kept 22 numerical coordinates, six indicators and two billing
frequency dummies. The retained missingness signals refer to issued amount,
mean invoice amount, days since last invoice and the three activity changes
for active users, sessions and events. The filter removed the unobserved-usage
month count, eight constant missing indicators and the launch plan dummy.
The CLV fitted representation contains 14 numerical coordinates and 15
one-hot coordinates. Its registry covers tenure, lifecycle, invoice amounts and
frequency, recency, cadence, snapshot amounts and coverage, and calendar
month. Account product usage and Phase 06 predictions are outside that registry.
Both fitted estimators lack a public `feature_importances_` property.
[Phase 05 registry](../../src/nowa_customer_intelligence/data/synthetic/feature_matrix.py),
[churn estimator and preprocessing](../../src/nowa_customer_intelligence/models/churn/estimators.py),
[CLV registry](../../src/nowa_customer_intelligence/models/clv/features.py),
[CLV fitted pipeline and clipping](../../src/nowa_customer_intelligence/models/clv/research.py).

The Phase 05 bundle under `data/processed/phase05-fieldwise-final/` matched
the Phase 06 manifest and internal evidence fingerprints. The bundle manifest
SHA-256 is `3f5f1e4768cd6965e6c900288954f5c9bb863f7c5aaed39fac27bafe34eede3eba`.
The Phase 07 seed-42 training and validation partitions were reconstructed
through the accepted development generator in temporary storage. Their frozen
row fingerprints reproduced exactly, including predictors, target states and
order.

| Reconstructed CLV partition | SHA-256 |
|---|---|
| Training | `d4bb8e8d84a8588c6643b368be701521f3171f3269acf732761a280b442051cb` |
| Validation | `b4a0cfa9326279c02c8fb9f49b577f26dd910e5ba464f57bad72d7e30a9c2978` |

Twelve evenly spaced validation indices per model were used solely for
interface checks. The fitted preprocessing and isolated estimator reproduced
each full pipeline. Applying the logistic link to churn margins reproduced
class-1 probabilities at absolute tolerance 1e-12. Clipped CLV predictions
matched the saved rows within £1e-9. The CLV probe encountered zero negative
pre-clip predictions. A separate toy calculation exercised a negative
pre-clip case. This establishes interface consistency on the audited rows.
The accepted predictive metrics were read from the frozen reports.

## Initial feasibility and approved output contracts

The audit environment is Python 3.12.3, scikit-learn 1.9.1, NumPy 2.5.4,
pandas 2.3.3, SciPy 1.18.1 and Joblib 1.6.0. Matplotlib 3.11.2, nbformat
5.11.1, nbclient 0.11.0 and ipykernel 6.31.0 are installed. The separate
notebook verification environment has scikit-learn 1.9.1 and NumPy 2.5.5.
SHAP and Numba were absent from both initial environments. The declared optional
range for SHAP is `>=0.46,<1.0`. The approved isolated check established a
compatible runtime as recorded under the executed research below. The frozen binaries load in
the inspected scikit-learn version. There were no dependency changes.

| Method | Approved research direction | Initial evidence and limits |
|---|---|---|
| Global permutation | Use the full clipped CLV predictor and change in validation MAE, in GBP. Compare coherent financial/lifecycle blocks before interpreting individual permutations. | Deterministic negative-MAE permutation worked on a toy estimator. Correlated features can substitute for each other. Weight by rows for the accepted MAE estimand and report an account-balanced sensitivity separately. |
| Churn reliance and errors | Prefer descriptive class-1 probability sensitivity and score/error-cohort summaries. Treat any AP/Brier permutation as explicitly underpowered diagnostics following separate approval. | Eight validation positive accounts and weak ranking prevent a reliable performance-importance ranking. Sensitivity describes score behaviour without attributing real cancellation drivers. |
| SHAP for tree estimators | When a test environment is approved, probe TreeExplainer on the exact fitted arrays, explicit perturbation mode and paired input order. Try raw outputs first. Verify shapes, expected values and additivity. Try interventional probability only if this exact classifier and SHAP version support it. | SHAP could not be imported locally. Actual estimator/explainer compatibility and probability support are unverified. The preprocessing pipeline must be handled explicitly. |
| Final-output additive alternative | For CLV prefer grouped model-agnostic Shapley contributions on the clipped full-pipeline output if TreeSHAP provides only pre-clip values. The same approach can explain the full class-1 probability callable. | An exact two-block toy game reconciled base and contributions on a clipped output. Full-model suitability, background sensitivity and feasible cost remain open. |
| PDP and ICE | Evaluate predictions directly on supported grids with the full predictor, including class orientation and clipping. Use account-balanced averages and an aligned subset of local curves. | Brute PDP equalled mean ICE on a numerical toy fixture. This scikit-learn version rejects integer numerical PDP input. Use float model inputs and integer support points for discrete counts, plus explicit supported categories when relevant. |
| Interactions and native importance | Begin with a small, predeclared set of supported pairs and two-way response differences. Consider SHAP interactions only after estimator, perturbation and scale tests. | Neither frozen estimator provides public impurity importance. Recorded tree structure may illustrate specific splits only. Full pairwise interaction enumeration and LIME add complexity without an identified need. |

Interventional TreeSHAP depends on the background and can separate correlated
coordinates. Tree-path-dependent explanations use a different reference
distribution. For an output-additive explanation use the same row and output
throughout, with `base + sum(contributions) = output(row)`. A logistic link
applies to the total churn margin. Component-wise logistic conversion does not
produce probability contributions. For CLV, a signed raw attribution explains
the pre-clip estimate. Under the final GBP contract, evaluate
`max(0, fitted_pipeline.predict(row))` for each background/coalition or use an
explainer that demonstrably targets that callable. Clipping the baseline or
components separately changes the result. Report the actual baseline as
expected output under the stated reference distribution. In the toy clipped
two-block test the base was 0, the contributions were 4 and 1, and the output
was 5. These are synthetic toy amounts.
[SHAP TreeExplainer documentation](https://shap.readthedocs.io/en/stable/generated/shap.TreeExplainer.html),
[scikit-learn permutation importance](https://scikit-learn.org/stable/modules/permutation_importance),
[scikit-learn partial dependence and ICE](https://scikit-learn.org/stable/modules/partial_dependence.html).

For transformed attribution, derive a positional lineage from
`ColumnTransformer.output_indices_`, fitted column lists, indicator positions,
fitted category levels and the selector mask. The probe checked the lineages
against `get_feature_names_out()`, the model width and full pipeline predictions.
One-hot levels and an original feature's missingness indicator may be summed
with its other components for an original-feature signed total within the
same additive game. That total is distinct from a Shapley attribution made on
an explicitly grouped original-space game. Sum before taking absolute values
for global mean absolute grouped attribution. Include both denominators and
grouping conventions. Feature-name string splitting alone cannot establish
lineage. Omit attribution for removed coordinates, documenting the fitted
filter and the supported categories.

## Reference, statistics and quality controls

Use checksum-bound seed-42 training evidence for background selection. The
frozen primary reference contains up to 64 distinct fitting accounts, one latest eligible
observation per account, with stable episode-key tie-breaking where needed.
Use proportionate cadence strata and seed 909. Preserve a background digest
and achieved support. Compare seeds 910 and 911 and sizes 32 and 128 where
support permits. An exact grouped callable game evaluates up to the number
of background rows times two to the power of the number of blocks per local
case. Limit the group count and local batch sizes before the approved pilot.
Consider repeated permutation paths with reported convergence if the exact
budget is infeasible. Local cases and error summaries can use the verified,
previously evaluated validation cohort. Keep customer IDs internal to selection and
grouping. A local case uses the fitted model for its own episode or account
with its original observation date and predictor lineage.

Select cases deterministically before computing explanations. For CLV,
use representative low- and high-error quantiles, monthly and annual
observations, a mature zero and a high historical-issuance example. Use
retained or reconciled error metadata, stable observation keys for tie-breaking
and deduplicate account appearances. For churn, choose limited diagnostic
cases by cohort and threshold outcome with visible positive support. Prevent
aesthetic selection and labelling of examples as retention recommendations.
Protected churn, CLV and segmentation reserves supply no background,
perturbation or selection evidence.

The CLV grouped permutation design uses 30 repeats with seed 912 and a
shared donor permutation over coherent fields. Match observation period and
evidence coverage where support allows, and use account blocks or a matched
single observation per account as a sensitivity check. Keep target and original
observation order fixed and report mean, spread and matched support. Use
account-level bootstrap or distinct-account resampling for sampling intervals.
Separate shuffle variability, resampling variability and prediction error.
For PDP and ICE, use supported grid values within predeclared training
quantiles and inspect observed support within key cohorts. Reject unsupported
joint combinations or show them separately as model stress tests. Examples
include invoice totals inconsistent with counts, incompatible cadence and
invoice dates, or impossible lifecycle/usage combinations. Mark precisely
which grid cells are admissible. These curves measure response to supplied
inputs. An actual counterfactual would require a feasible intervention model.

Predeclare the exact output callable, feature contract, model and input
hashes, shape, order, comparison tolerance, background, case selection and
computational budget. The executed research applied the following controls.

- Compare complete-pipeline predictions and target-unit outputs against
  checksum-verified development evidence. Reject missing/reordered fields,
  shape and class mismatches, and non-finite values at the proper boundary.
- Require finite, dimensionally exact additive decompositions per row.
  Frozen absolute residual tolerances are 1e-8 on the probability
  scale, 1e-7 on log odds and £1e-6 on the final GBP scale. Freeze tolerances
  before research and record maximum residual and failures. Any different
  tolerance must have an explicit precision and computational rationale.
- Repeat on identical hashed inputs to test deterministic reproduction.
  For background and account sample sensitivity report signed local spread
  and sign consistency, top-five Jaccard overlap and tied-rank Spearman
  agreement on aggregated global magnitudes. Treat near-zero signs and tied
  or unsupported comparisons as indeterminate. Diagnostic floors are median global rank correlation 0.80 and top-set
  overlap 0.60. The top set is capped at half the tested coordinates
  where fewer than ten are available. Report dispersion and
  instability at small support. Stability evidence does not repair the
  limitations of the fitted models.
- Keep report schema, environment, hashes, permutation and SHAP settings,
  perturbation direction, grouping, exclusions, costs, artefact fingerprints
  and limitations. Run small offline tests for identity, invalid input,
  feature order, category/indicator lineage, reserve isolation, shape, class
  orientation, clipping, additivity and deterministic sampling. Cover report
  tampering and notebook replay without fitting. Validate actual estimator
  SHAP and stability only in the authorised research stage.

## Approved owner decisions

| Decision | Status | Implemented policy |
|---|---|---|
| XAI-PO-001 — Explainability scope | Approved | CLV billed-value research first, churn diagnostic research and deterministic RFM documentation. |
| XAI-PO-002 — Explanation methods and conditional fallback | Approved | Churn probability TreeSHAP with a separate log-odds result, verified preprocessing, CLV clipped-output grouped Shapley, matched-account MAE permutation, supported PDP/ICE and interaction diagnostics. |
| XAI-PO-003 — Reference populations and background sampling | Approved | Only accepted training and previously evaluated development validation. One latest fitting row per reference account with cadence-stratified sampling. Local examples use predefined roles and distinct accounts. |
| XAI-PO-004 — Explanation validation and quality controls | Approved | Frozen input hashes, complete prediction reconciliation, attribution width and positional grouping, scale-specific tolerances, fixed research protocol, deterministic replay and background/account stability tests. |
| XAI-PO-005 — Business interpretation restrictions | Approved | Internal model-behaviour interpretation with economic and predictive limits. Operational risk, customer interventions, causal effects and revenue exposure remain out of scope. |

### Business and risk interpretation

Phase 06 AP is close to its 1.116% validation prevalence, ROC-AUC is below
0.5, and 695 of 703 alerts were false positives. Eight positive validation
accounts are below the original floor of ten. Neither global attribution nor
a faithful local breakdown establishes predictive utility or independent
generalisation. Phase 07 exhibits better validation MAE than the baseline on
fictional development data, with a considerable RMSE and recurring synthetic
billing patterns. Its billed-value target remains separate from cash,
recognised revenue, margin and lifetime value.

The planning proposal for exposure would require a calibrated event probability
and a defensible conditional loss over a common horizon and unit of analysis.
The churn score concerns a 30-day episode event, while the CLV estimate concerns
aggregate six-month account issuance across episodes. A defensible model also
needs overlap treatment, financial loss attribution, conditional exposure when
the event occurs, and validation before operational use. Any exposure estimate,
risk band, recoverable value or uplift claim requires additional evidence and
separate owner approval. [Modelling strategy](modelling_and_evaluation_strategy.md#6-revenue-at-risk),
[documentation approval record](../07_project_management/documentation_review_and_approval.md).

Phase 08 ended without a model nomination. Explain RFM in this scope document
and refer to the accepted notebooks and frozen boundary record. RFM uses known
issued invoices within the approved window, ties share a band, and mixed
cadence was unsupported for a separate score. For example, a fictional monthly
case at 12 recency days, 12 invoices and £948 maps to 3–1–1 under the traditional
cuts and 2–1–1 under the monthly-specific cuts. This illustrates billing-cadence
interpretation. Research cluster labels remain unsuitable as approved customer
segments. No clustering rerun or Phase 08 reserve access forms part of XAI.
[Phase 08 decision and validation record](phase08_segmentation_scope_and_validation.md).

## Implementation and notebook delivery

The existing `src/nowa_customer_intelligence/explainability/` package contains
frozen-evidence interfaces, bounded methods and the research/provenance runner.
The notebooks replay checksum-verified local reports with cleared repository
outputs. They neither load fitted estimators nor generate explanations. Record the model, feature contract,
input/output hashes, time boundaries, method options, background seed, settings,
computed budget, validation and stability evidence before publication. Keep
generated reports, model binaries and executed notebook copies outside Git.

The approved numbered notebooks were implemented in the existing phase-folder
structure. They display audited figures and worked examples.

- [Notebook 11, churn explainability](../../notebooks/06_explainable_ai/11_churn_model_explainability.ipynb) begins
  with a diagnostic executive summary, contractual episode target and weak
  predictive evidence, then the frozen pipeline and feature dictionary.
  Explain importance and additive mathematics, log odds and probability,
  global and local interpretation, supported interactions, PDP/ICE,
  stability, sparse-positive error cohorts and generator-pattern diagnostics.
  Show score and calibration context, labelled contribution bars and selected
  probability-sensitivity curves only when validated. Close with limitations
  on customer-risk conclusions.
- [Notebook 12, billed-value explainability](../../notebooks/06_explainable_ai/12_clv_model_explainability.ipynb) begins
  with an executive financial dashboard, billed-value definition, frozen
  pipeline and dictionary. Cover MAE permutation by block, additive methods
  and background, signed versus clipped output, global magnitudes, local
  account plots, supported interactions and sensitivity. Reconcile selected
  waterfalls to predictions, then show errors by cadence/value group,
  background and account-level stability, correlated features, synthetic
  generalisation and business limitations.

Each figure should identify its population, frozen model and output units,
explanation method, uncertainty where applicable and permissible conclusions.
Include worked mathematical examples, statistical tables and provenance.
[Notebook conventions](../../notebooks/README.md).

Fresh Python 3.12 kernels completed both executed review copies. Notebook 11
contains 17 Markdown cells, 15 code cells and 18 figures. Notebook 12 contains
19 Markdown cells, 17 code cells and 23 figures. The copies preserve the exact
analytical cell sources. Repository execution counters and outputs are cleared.

## Executed research and validated outputs

### Technical gates and frozen evidence

The separate Python 3.12.3 environment used NumPy 2.5.4, scikit-learn 1.9.1,
pandas 2.3.3, SciPy 1.18.1, Joblib 1.6.0, SHAP 0.54.1 and Numba 0.68.1.
SHAP imported and a small Numba JIT operation ran. The project environment and
dependency specifications were unchanged. The retained model hashes in the
inventory matched before and after execution. The audited prediction contract
reconciled all **717 churn** and **355 CLV** development-validation predictions
with their accepted interfaces. Churn reproduced accepted metrics and class
orientation. CLV reproduced every saved clipped validation prediction.
Three of the full set of signed CLV predictions were negative before clipping.

The checksum-bound compatibility gate used 32 training accounts and 12
deterministically spaced validation probes. Interventional TreeSHAP passed
for churn on both scales, with 30 transformed coefficients and a scalar
base per row. CLV interventional raw decomposition missed by at most
**£9.66** and failed 12 of 12 checks at £1e-6. CLV path-dependent TreeSHAP
matched signed raw predictions within £1.14e-12 on the probe. Its training
path reference and pre-clip output differ from the approved account-balanced
final-output study. It is retained as compatibility evidence only. The
interventional discrepancy arose on signed predictions before clipping,
and its technical cause remains unresolved. The delivered CLV method is
grouped model-agnostic attribution on the complete clipped callable.

| Delivered decomposition | Rows | Maximum absolute error | Mean absolute error | Tolerance | Failures |
|---|---:|---:|---:|---:|---:|
| Churn TreeSHAP, class-1 probability | 98 | 2.51e-9 | 5.07e-10 | 1e-8 | 0 |
| Churn TreeSHAP, class-1 log odds | 98 | 4.21e-8 | 1.48e-8 | 1e-7 | 0 |
| Churn finite block game, class-1 probability | 98 | 1.11e-16 | 1.96e-17 | 1e-8 | 0 |
| CLV finite block game, clipped GBP | 102 | £1.14e-13 | £1.18e-14 | £1e-6 | 0 |

Original-feature grouping conserved transformed churn contributions within
1e-12 before comparing to the model output. The finite game uses the mean
of the exact output over the prespecified background as its base. The local
clipped case has a signed raw forecast of about **−£3.83**, a final forecast
of **£0.00**, and a grouped decomposition that reconstructs **£0.00**.

### Audited CLV cooperative game

The four blocks below partition the 17 raw predictors in the frozen Phase 07
feature registry. Account keys, invoice outcomes and future observations
are excluded from the model input. Account keys serve only to select and
group observations.

| Block | Original features |
|---|---|
| Account lifecycle | `tenure_days`, `episodes`, `completed`, `reactivated`, `active` |
| Invoice history and cadence | `invoice_count`, `issued_gbp`, `recent_gbp`, `mean_invoice_gbp`, `recency_days`, `monthly`, `annual`, `billing_evidence`, `cadence` |
| Contract snapshots | `snapshot_gbp`, `snapshot_coverage` |
| Calendar | `month` |

For an explained row $x$, a coalition $S$ of the four blocks $G$, and a
background row $b \in B$, construct $z(x,b,S)$ before preprocessing. Use
$x$ for every field in $S$ and the same $b$ for all remaining fields. The
signed predictor $h$ applies the original fitted preprocessing and
regressor to the 17 fields in registry order. Clip each hybrid's prediction
individually and average it with equal weight across the 64 reference rows.

$$
f(z)=\max(0,h(z)), \qquad
v_x(S)=\frac{1}{|B|}\sum_{b\in B} f(z(x,b,S)).
$$

The empty coalition is the mean final prediction over $B$ (£486.65 for
the primary reference). The full coalition returns the final prediction
for $x$. The implementation evaluates all 16 coalitions, using these two
endpoints directly. For block $j$, each coalition without $j$ contributes
its incremental change with weight $1/[4\binom{3}{|S|}]$. These are
the fractions of the 24 insertion orders with each predecessor set.

$$
\phi_j(x)=\sum_{S\subseteq G\setminus\{j\}}
  \frac{v_x(S\cup\{j\})-v_x(S)}{4\binom{3}{|S|}}, \qquad
f(x)=v_x(\varnothing)+\sum_{j\in G}\phi_j(x).
$$

The reference keeps relationships within each borrowed block and among
the jointly borrowed blocks. Mixing them with held blocks can still
create historically implausible combinations. The contributions are
specific to this game, predictor and reference. They provide no causal
evidence, unique individual-field effects within a block, independently
identified effects of correlated billing variables or real-customer
generalisation.

### Frozen samples and development results

The primary training background contains 64 distinct accounts for each model.
Churn has 48 monthly and 16 annual references, and CLV has 50 monthly and
14 annual references. Churn's 64 rows include 61 from February 2023,
two from January and one from December. All CLV references are from
June 2022. Selecting the latest row per account concentrates each reference
at the end of training. Baselines and contributions reflect those dates
and their cadence mix. The test offers limited evidence across time.
Global results use 96 distinct validation accounts per model, with one
latest eligible row per account. Seven CLV and four churn local
roles are selected deterministically on distinct accounts. Cases outside
the global sample are appended to the explained inputs. The report retains
composition, anonymised cases and background/input fingerprints. It carries
no customer or episode identifiers.

The CLV invoice history and cadence block averaged **£112.16** in absolute
attribution. Account lifecycle averaged **£22.68** and calendar **£11.54**.
Contract snapshots were effectively zero under this decomposition.
The grouped permutation used all 355 January and February 2023
development-validation rows from 180 accounts. Its **£58.27** unperturbed
row-weighted MAE is the accepted validation MAE on the same rows and
weighting. The equal-account baseline was **£57.47**. For each of 30
draws from seed 912, the runner shuffled donor accounts within strata of
identical ordered observation dates and exchanged complete block
trajectories. All 180 accounts were movable. The full clipped predictor
scored each hybrid against the original mature issuance, and the mean
absolute error minus the unperturbed MAE gave each row-weighted change.
The same donor draws were used for each block and singleton. The reported
sample SD uses 29 degrees of freedom.
Invoice history and cadence increased MAE by **£138.05** on average
(SD **£9.06**), and account lifecycle by **£5.36** (SD **£1.28**). These
are changes in prediction error in GBP. Joint swaps preserve within-block
relationships but can produce implausible combinations with fields left
unchanged. Snapshot permutations changed values and left MAE unchanged.
Calendar could not move under the matched-time design. Singleton recency, a
stress test disrupting financial relationships, increased MAE by £101.86
on average. The joint evidence cannot isolate the effect of cadence,
recency or any financial field as causal. Annual validation MAE was **£120.72**
on 81 rows and monthly MAE was **£32.13** on 266 rows. The mixed group had
eight rows across four accounts. The largest-error local example had a
forecast of **£473.41** and recorded **£1,327.20**. The high-forecast
mature-zero case predicted **£734.19** against **£0.00** recorded.

Churn's leading mean absolute probability contribution was episode age
(**0.11781**), followed by latest sessions (**0.01816**) and expected usage
months (**0.01478**). Their association and the score response to age merit
synthetic-generator diagnosis. The model assigned about **0.9191** to the
selected false positive. The selected confirmed positive was at the
research threshold, approximately **0.003965**. These examples illustrate
the separation between mathematical reconciliation and weak predictive
validity. A performance permutation ranking was withheld because there
were only eight positive accounts.

One-way sensitivity uses deduplicated nearest training quantiles at
10%, 25%, 50%, 75% and 90%, or the observed categorical levels. Two-way
grids use 10%, 50% and 90% for numerical features. For each modified row
the screen requires a complete training neighbour within the selected
cadence and a maximum coordinate distance of 0.30 within-cadence training
IQR units. Where an IQR is zero, the implementation uses the training
range with a floor of 1e-9. The screened rows use the frozen class-1
probability or clipped GBP predictor. Each PDP point averages eligible
ICE predictions out of 96 candidate accounts and requires at least five.
Consequently the denominators can differ across points.
Both models have supported numerical responses. Churn's annual-cadence
replacement had no supported global point under this screen. None of
the four predeclared two-way grids had five accounts at all four corners
of a local contrast. No account passed the screen at every corner of
any adjacent contrast. Joint support and available cell means are shown
as model-response diagnostics. The support screen cannot enforce every
relationship among correlated fields.

Identical-background attribution replay gave zero maximum change for both
models. Compare each alternative background (64 accounts at seeds 910 and
911, and 32 and 128 accounts at seed 909) with the primary ranking on
the same 96 validation accounts. Each of 100 bootstrap draws at seed 913
instead uses the fixed primary background and samples 96 account
representatives with replacement. Compute ranks from mean absolute
contributions for the 23 churn features with retained coordinates or four
CLV blocks. Median tied-rank Spearman over the four backgrounds and 100
bootstrap draws was **0.984** and **0.995** respectively for churn, and
**1.000** in both comparisons for CLV. Median top-set Jaccard was
**1.000**, using five churn features and two CLV blocks. Across all
explained rows and contribution columns, a background change shifted one
attribution by up to **0.07225 probability** for churn or **£24.15** for
CLV. Global rank agreement can coexist with meaningful local reference
sensitivity. These diagnostics measure explanation sensitivity on fixed
models. Predictive uncertainty and temporal generalisation require
separate evidence.

The runner writes the protocol before it generates complete evidence.
The protocol fixes seeds, cohorts, case rules, group partitions, support
rules, methods, tolerances and the failure policy. The isolated workspace
contains `protocol.json`, `compatibility.json`, `churn.json`, `clv.json`
and `manifest.json`. A second run of the same protocol reproduced all
numerical evidence and case selections after anonymised error-cohort
reporting was added. The first run is retained outside Git. [Notebook
execution and isolated environment instructions](../../notebooks/README.md#phase-09-explainable-ai).

## Acceptance matrix

The Project Owner's conditional engineering acceptance applies to the
frozen-model explanation implementation, synthetic CLV and churn research,
output reconciliation, feature lineage, stability diagnostics, notebooks and
reproducible evidence. Commercial financial use, validated churn ranking,
operational scoring, causal interpretation, revenue-at-risk, interventions
and production deployment remain outside the accepted scope.

The final audit passed 87 targeted tests, including 15 Phase 09 checks,
and 1,147 repository regression tests. The historical Batch 09 model-fitting
integration was excluded. An editor autosave interrupted the first full
regression. The complete rerun used a byte-verified snapshot. Both notebooks
also ran in fresh kernels and rendered 18 churn and 23 CLV figures. Ruff lint
and format, dependency consistency, notebook schemas, relative links and
whitespace checks passed. The 40 retained non-reserve checksums and both
Phase 09 report manifests' contents matched. The final audit reused saved
predictions and investigated the maths, sampling and support with offline
fixtures. It performed no model refitting, rescoring or protected reserve
access. The Phase 06 holdout remains unscored, the previously scored Phase 07
reserve evidence is preserved and Phase 08 still has no nominee or reserve
model score.

| ID | Requirement | Result | Evidence |
|---|---|---|---|
| XAI-01 | Approved scope | Passed | XAI-PO-001 through XAI-PO-005 recorded. |
| XAI-02 | Frozen model provenance | Passed | Both accepted designs, reports and model binaries verified before deserialisation. |
| XAI-03 | Valid reference populations | Passed | Rebuilt seed-42 training and accepted development-validation sample fingerprints without scoring. |
| XAI-04 | Feature contract and transformation integrity | Passed | Churn 25→40→30 and CLV 17→29 mapped positionally. |
| XAI-05 | Output-scale interpretation | Passed | Independent margin, class-1 probability and clipped GBP checks. |
| XAI-06 | Global explanation methodology | Passed | Observed-cohort contribution summaries, grouped and singleton CLV permutation, and recorded support limits. |
| XAI-07 | Local explanation methodology | Passed | Deterministic anonymised cases and output reconciliation. |
| XAI-08 | SHAP or justified alternative | Passed with documented limitations | Churn TreeSHAP reconciled on both scales. CLV interventional raw TreeSHAP failed and the audited clipped four-block game is used. |
| XAI-09 | Permutation Importance or alternative | Passed with documented limitations | The CLV matched-account permutation used the accepted MAE population. Calendar could not move. Churn performance permutation was withheld for sparse positives. |
| XAI-10 | PDP and ICE feasibility | Passed with documented limitations | Supported grid responses reported with variable denominators. Matched interaction contrasts lacked support. |
| XAI-11 | Additivity and consistency | Passed | Zero tolerance failures on all delivered modes, with the unreconciled CLV tree configuration excluded. |
| XAI-12 | Stability | Passed with documented limitations | Identical replay, background comparison and account bootstrap executed. Local contributions remain reference-dependent. |
| XAI-13 | Churn predictive-validity limitations | Passed | Eight positive accounts, weak ranking and false positives remain explicit. |
| XAI-14 | CLV economic interpretation | Passed | Six months of gross issued GBP, with clipping and billing context. |
| XAI-15 | Segmentation and RFM interpretation | Passed | Deterministic RFM and the Phase 08 negative nomination preserved. |
| XAI-16 | Correlation and causal-inference limitations | Passed | Joint blocks, measured support and descriptive sensitivity with limitations. |
| XAI-17 | Comprehensive churn notebook | Passed with documented limitations | Frozen report replay and mathematical diagnostics. Sparse-positive performance-ranking limit documented. |
| XAI-18 | Comprehensive CLV notebook | Passed with documented limitations | Scoped GBP plots and reconciled fallback. Unsupported per-feature CLV TreeSHAP excluded. |
| XAI-19 | Automated tests and reproducibility | Passed | Four-block fixture, targeted and full regression checks, and fresh-kernel replay. |
| XAI-20 | Preservation of prior phase boundaries | Passed | Accepted checkpoints and retained artefacts preserved. Phase 10 remains pending. |
