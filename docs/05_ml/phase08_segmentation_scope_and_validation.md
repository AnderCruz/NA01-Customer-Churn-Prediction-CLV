# Phase 08 customer segmentation scope and validation

## Authority and approved owner decisions

The Project Owner approved SEG-PO-001 through SEG-PO-005 and controlled Phase 08
fitting and stability refits. Phase 08 engineering and experimental research
are accepted and completed with documented limitations and negative model
nomination following final reconciliation and verification.
The experimental users are Customer Success and Revenue Operations. BO-03,
FR-026–028 and AC-010 call for interpretable, documented customer profiles and
reviewable labels. Review covered NEDS v1.1, the repository roadmap, Customer
Data Contract v1.1, the accepted ADRs, Phase 03 acquisition evidence, prior
notebooks and tests, the Phase 05 feature registry, and accepted Phase 06–07
evaluation and financial implementations. The standalone Project Charter and
complete approved 14-phase roadmap were unavailable. The owner brief and
repository roadmap establish sequencing.
[Business objectives](../01_business/business_objectives_and_scope.md),
[requirements](../02_requirements/functional_requirements.md),
[contract](../04_data/customer_data_contract.md),
[episode identity](../03_architecture/adr_episode_identity_and_identifier_management.md),
[Phase 06 protocol](phase06_churn_evaluation_protocol.md),
[Phase 07 economic definition](phase07_clv_economic_definition_and_validation.md).

| Decision | Status | Operational implementation |
|---|---|---|
| SEG-PO-001 — Purpose and customer eligibility | Approved | One visible canonical account at UTC month end. Primary eligibility requires its complete 12-calendar-month window inside a verified fictional source and the essential financial fields. Accounts with no active subscription remain in scope where evidence permits. |
| SEG-PO-002 — Traditional and cadence-aware RFM | Approved | Exact gross issuance, visible qualifying invoice count and elapsed UTC days. Freeze overall and supported cadence-specific score bands on the development fit date. |
| SEG-PO-003 — Point-in-time account usage | Approved | Observe three fixed completed calendar months. Use only dated, available, complete records attributable to one whole-month active episode. Exclude ambiguous multiple-episode evidence. |
| SEG-PO-004 — Feature space, clustering and assignment | Approved | FS-01 financial, FS-02 financial and contractual, and FS-03 conditional on usage feasibility. Compare StandardScaler-weighted K-Means, Ward and diagonal Gaussian mixtures, with explicit cadence sensitivity and native assignment where supported. |
| SEG-PO-005 — Independent evaluation and temporal stability | Approved | Count-only chronological feasibility, controlled refits and frozen validation. Keep a separate seed-83108 reserve for evaluation only after nomination. |

Commercial segment definitions, minimum service levels, operational refresh,
actions and real-customer validation require separate evidence and approval.
Gross issued GBP measures invoice issuance. Collection, recognition, margin,
lifetime value, satisfaction, retention and loyalty are separate concepts.
Misata and UCI, earlier reserves, model predictions, realised outcomes,
canonical identifiers and post-observation facts stay outside clustering.

## Evidence and eligibility implementation

Each reference reconstruction passes the existing development acceptance and
integrity checks for the five source exports. File fingerprints, bounded
generator history, policy and scenario metadata and the Registry fingerprint
are recorded. Eligibility depends on this exhaustive fictional source
attestation and the as-of ledger. Calendar headroom alone is insufficient for an
unverified source. Visible dispositions are eligible, short history, insufficient
source evidence and unavailable essential financial features. Not-yet-visible
counts reconcile to the extraction roster in an aggregate retrospective audit.
The financial ledger preserves distinct episodes and unique invoice attribution.
It gates facts by effective, occurred and available times.

The financial window is (t−12 calendar months, t] in UTC. Leap-day anniversaries
clamp to the last valid day. Date-only invoice issues use UTC midnight. Recency
takes the latest qualifying known issue even outside the window. Unknown
recency is unassignable. A verified feed with no known in-window issues
supports observed zero frequency and issuance, with undefined recency if no
prior issue is visible. Short histories retain only descriptive amounts.

Traditional and cadence-aware RFM use nearest-rank empirical thirds. Duplicate
cut values and cuts producing a band smaller than five accounts or 5% of the
group are pooled. Equality stays in the lower raw band. Each dimension uses
three levels 1–3, two levels 1 and 3, or one neutral level 2. Recency has
reverse score direction. Values outside the development range map to the outer
frozen band. The cadence method needs 30 development accounts in a group.
Monthly, annual and mixed are historical issue cadences. Unsupported groups
remain unassignable even if their later populations grow. Within-cadence
scores express position in that cadence's distribution.

Usage is at episode grain, with no distinct account user, session or event
union. The three periods end on the closed observation month. A full usable
account period needs one known episode throughout and one available record
with all three count fields. A second overlapping episode, including an
intra-month successor, requires unknown counts for that period. Keep structural
absence, partial periods, missing evidence and awaiting the scheduled report
distinct. Observed zero remains a count. Latest and mean use available
comparable periods and carry coverage. End-to-end changes require both fixed
endpoints. The synthetic publisher makes completed usage available no earlier
than the next day. The month window stays fixed as coverage is measured.

## Frozen protocol `fieldwise-segmentation-v0`

- **Dates and support.** Prefer 31 March 2023 fit, 31 December 2023 validation
  and 31 March 2024 assessment. Require 200 primary eligible accounts and two
  cadence groups with at least 30 accounts at each date. If preferred dates are
  infeasible, use the earliest supported chronological pair at least three
  months apart and before the fixed assessment by at least three months.
  Choice uses only coverage and support. March 2024 was inspected
  descriptively in earlier work.
- **Feature spaces.** FS-01 uses raw recency, frequency and monetary value.
  FS-02 adds tenure, known reactivation and cadence indicators. A predeclared
  FS-02 variant removes explicit cadence while keeping contractual numerics.
  FS-03 would add mean users, sessions and events from complete windows.
  It requires three of three usable months on at least 80% of eligible fit and
  validation accounts and five distinct development values in each admitted
  measure. Usage coverage, status and source metadata are diagnostic.
  Phase 05 and Phase 07 registries are unchanged.
- **Scaling.** Convert exact GBP at the model boundary. Reject essential missing
  values and unsupported explicit categories. Drop training constants.
  Standardise continuous coordinates. Use unstandardised one-hot cadence to
  avoid amplifying rare levels. Divide each block by the square root of its
  effective dimension. This averages squared coordinate contributions within a
  block and does not guarantee equal realised variance or eliminate correlation.
  Diagonal Gaussian likelihood can respond differently to the same weights.
  A robust sensitivity scaler was considered. The controlled comparison varies
  feature blocks and cadence while keeping one primary scaler. PCA is fitted on
  the development representation for diagnostics, with full coordinates retained
  for clustering.
- **Fixed candidates.** K-Means uses k-means++, 20 starts, 300 iterations and
  tolerance 0.0001. Ward agglomeration uses Euclidean distance and a complete
  hierarchy, with no native transfer assignment. Diagonal Gaussian mixtures use
  10 starts, 200 iterations, tolerance 0.001 and covariance regularisation
  0.000001. Test 2–6 groups and primary seed 42. Preserve family-specific metrics.
- **Stability.** Refit supported, converged candidates with seeds 11, 29 and 73
  where applicable. Draw 20 deterministic 80% account subsets with seed 602.
  Compare each to the original partition on the same accounts using ARI. Each
  subset has one refit with frozen preprocessing and one refit of the complete
  workflow. Experimental floors are minimum initialisation ARI 0.75, median
  subsample ARI 0.75 and 10th percentile 0.60 in both modes. Preserve failures.
- **Nomination.** Require native assignment, convergence, at least 30 and 5% per
  cluster, and 95% coverage of the primary eligible population at fit and
  validation. Require stability and common financial-space silhouette of at
  least 0.20 at both dates. For interpretability reject any fixed generator
  reference NMI above 0.65 or cadence homogeneity above 0.75. References are
  cadence, fixed annual age bands, reactivation, active count, catalogue amount
  and complete history. These are engineering screening thresholds. Compare
  survivors by higher development common-space silhouette. Within 0.02,
  prefer higher frozen validation ARI on shared accounts, fewer groups,
  simpler family and smaller feature space. Permit a negative result.
- **Confirmation.** Seed 83108 uses an isolated fictional client namespace,
  Registry, export and manifest. The reserve month end is fixed at 31 March
  2024. Only schema, primary eligibility and source coverage counts precede
  selection. Freeze the nominee, labels and preprocessing before evaluation.
  Apply the same procedure to both later snapshots and only the frozen nominee
  to the reserve. Preserve unscored reserve evidence when no nominee passes.
  The other phase reserves are excluded. Same-generator transfer is fictional.

## Final evidence reconciliation

At the 31 March 2024 cut-off, the three expected months contribute 1,000
canonical account-months each. The rows below represent mutually exclusive
statuses, in the order used to resolve overlapping conditions.

| Status | Definition at the observation cut-off | January | February | March | Total |
|---|---|---:|---:|---:|---:|
| No known active episode | No known active episode overlaps the month. | 53 | 29 | 0 | 82 |
| Multiple episodes | More than one known episode overlaps the month, including intra-month succession. Account counts stay unknown. | 16 | 7 | 11 | 34 |
| Partial episode or record | One known episode overlaps the month with incomplete calendar coverage, or its available record has shorter period bounds. | 32 | 24 | 22 | 78 |
| Observed | One known episode spans the month and an available full-month record supplies all three counts. This includes measured zero counts. | 899 | 940 | 0 | 1,839 |
| Awaiting reporting | A whole-month episode has no usable row and the scheduled publication date is after the cut-off. | 0 | 0 | 967 | 967 |
| Missing or unavailable | The reporting date has passed and the required evidence is absent or unavailable. Periods before the covered source window also remain unavailable. | 0 | 0 | 0 | 0 |
| **Total** | | **1,000** | **1,000** | **1,000** | **3,000** |

The earlier summary omitted the 82 periods with no known active episode and
the 78 with partial coverage. The audit reproduced all five development
source fingerprints using a copy of the retained Registry and checked the
classifications against episode facts and actual usage availability
timestamps. Of the 1,839 observed periods, 257 had a measured zero in at
least one count field. Financial and contractual profiles and eligibility
were identical with usage included and omitted. The complete status table
corrects the reporting omission. The implementation and frozen results are
unchanged.

At each of the three approved UTC month-end cut-offs, the window includes
the closing month. Its usage becomes available no earlier than the next UTC
day under the one-day source lag. Each window therefore lacks a usable
closing month, even for a fully active account with complete earlier months.
Structural absence, partial periods and ambiguity also reduce usable
history. FS-03 remains excluded. **Three latest complete and available
reporting months** is a deferred investigation subject to separate Project
Owner approval. The approved fixed calendar policy remains in force.

### Candidate disposition

All 45 candidates were evaluated against the frozen protocol. The first
recorded rejection column counts each candidate once in the existing
evaluation order. The all-occurrences column includes overlapping gates.

| Rejection reason | First recorded | All occurrences |
|---|---:|---:|
| Development group support | 28 | 28 |
| Development separation | 2 | 13 |
| Native assignment unavailable | 4 | 15 |
| Validation group support | 0 | 16 |
| Validation separation | 2 | 10 |
| Stability | 0 | 3 |
| Generator association | 9 | 41 |
| **Total** | **45** | **126** |

Seventeen supported configurations advanced to stability assessment. All
three stability failures also failed another gate. Every candidate fitted
successfully and all iterative candidates converged. No development label
set was degenerate. Assignment coverage passed for candidates with native
assignment.

## Formal limitations

- All clustering candidates failed at least one nomination gate. Operational
  segment assignment and deployment remain unapproved.
- The fictional catalogue has limited price variation. Several stable
  clustering solutions track known generator characteristics, including
  cadence, contractual rate or reactivation. Stability alone provides
  insufficient evidence of meaningful customer heterogeneity.
- Conventional RFM is sensitive to billing cadence. Mixed cadence lacked
  development support for its own rule. RFM scores describe relative
  financial profiles. Churn risk, loyalty and customer actions require
  separate validation.
- The fixed behavioural window failed complete-coverage requirements.
  Full behavioural segmentation remains unavailable. The source lag is a
  structural limitation of the approved calendar window.
- March 2024 model transfer and independent seed-83108 evaluation were
  conditional on nomination. March has historical financial-reference
  assessment, and the reserve remains unscored.
- No real-customer validation or commercial effect on retention, engagement
  or revenue has been demonstrated. Production and commercial approval
  remain outside this scope.

## Deliverables

[Notebook 09](../../notebooks/05_customer_segmentation/09_rfm_and_customer_profiling.ipynb)
contains population, financial, RFM and usage analysis.
[Notebook 10](../../notebooks/05_customer_segmentation/10_customer_clustering_and_validation.ipynb)
contains fitted experiment evidence, model comparisons and the disposition of
transfer and reserve evaluation. Both use checksum-verified local reports.
