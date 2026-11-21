# Notebooks

Use numbered notebooks for exploration and experiments. Promote reusable logic into `src/`; avoid treating notebooks as production pipelines.

## Phase 04 data understanding

Use the project Python environment with the notebook extras installed, for example
`python -m pip install -e '.[notebooks]'`. Start the kernel from the repository root
or a subdirectory. Run each notebook from top to bottom in a fresh Python 3 kernel.

1. [Customer and subscription EDA](01_data_understanding/01_customer_subscription_eda.ipynb)
2. [Churn distribution and cohort analysis](01_data_understanding/02_churn_distribution_and_cohort_analysis.ipynb)
3. [Revenue, usage and temporal analysis](01_data_understanding/03_revenue_usage_and_temporal_analysis.ipynb)

Fieldwise is reconstructed through the supported development interface in a temporary
workspace. Notebooks 1 and 3 verify the approved local Misata and UCI files, respectively.
Use the separate [source acquisition commands](../docs/04_data/data_sources_and_governance.md#82-local-acquisition-and-analytical-access)
to prepare missing inputs before opening a notebook. Notebook execution is offline.

For automated end-to-end verification, execute each file with `nbclient` in its own
kernel using the notebook directory as the working directory. Store executed copies
outside Git. The repository notebooks contain source cells only. The retail notebook
streams both sheets twice, once for source validation and once for descriptive aggregation.

Use a clean Python 3.12 environment for verification. The notebooks do not use
PySpark. An unrelated PySpark installation in a shared environment can cause
Pandera to load an incompatible optional backend.

## Phase 05 feature engineering

[Fieldwise Cloud feature engineering analysis](02_feature_engineering/04_feature_engineering_analysis.ipynb)
uses the accepted bundle under `data/processed/phase05-fieldwise-final/`. Prepare
that local input using the [documented replay procedure](../docs/07_project_management/implementation_plan_and_roadmap.md#182-local-replay-and-integrity)
and the established Phase 05 Registry if the bundle is absent. A fresh Registry
creates different canonical IDs. The notebook reads and verifies the retained
bundle without opening the Registry or acquiring data.

Use a fresh Python 3.12 kernel with the notebook extras above. Executed copies
should remain local and outside Git. Outcomes are used for aggregate cohort
counts and do not enter the predictor analysis.

## Phase 06 churn modelling

1. [Churn baseline models](03_churn_modelling/05_churn_baseline_models.ipynb)
2. [Churn advanced models](03_churn_modelling/06_churn_advanced_models.ipynb)

The [evaluation protocol](../docs/05_ml/phase06_churn_evaluation_protocol.md) defines
the fixed split, evidence gates and candidate menu. Use the prepared reference artefacts
in `data/processed/phase06-research/results/`, or follow the controlled replay below.
In a Python 3.12 environment with the notebook extras, start a fresh kernel from the
repository or a notebook subdirectory. Run each notebook top to bottom. Both read
checksum-verified JSON and render offline. They do not load the fitted model or train.

To reproduce the research on a fresh local workspace, first prepare the Phase 05
bundle as described above. Use the same workspace path for both commands.

```bash
python -m nowa_customer_intelligence.models.churn.research prepare \
  --workspace data/processed/phase06-replay
python -m nowa_customer_intelligence.models.churn.research run \
  --workspace data/processed/phase06-replay
```

Inspect `design.json` after preparation. It records the evidence gate, partition support
and input fingerprints before fitting. When the confirmation gate fails, the run
records development metrics only. `--development-only` on `prepare` omits the reserve
entirely and is suitable for replay after a reserve has already been scored. A new
Registry changes the synthetic UUIDs and manifest fingerprints. Read existing
confirmation results instead of recreating and re-scoring the same fixed seed.

For a workspace other than the default, set `NCI_CHURN_RESULTS` to the absolute path
of its `results/` directory in the notebook kernel environment. The research command
allows one fitting run per prepared workspace. An interrupted run retains its
`run-started.json` and, if selection finished, its `frozen.json`. Preserve those
records. If the interrupted run could have reached reserve prediction, treat that
reserve as consumed and replay only in development mode. Keep the reports, model
binary, Registry and executed notebook copies local and outside Git.

## Phase 07 customer lifetime value modelling

[Historical customer value and baseline feasibility](04_clv_modelling/07_clv_historical_value_and_baselines.ipynb)
reconstructs the accepted Fieldwise Cloud scenario offline with a temporary
Registry and export directory that are removed after loading. Use the Python 3.12
notebook environment described above and run the source in a fresh kernel. Keep
executed copies outside Git. Monetary aggregates are Decimal GBP and the figures
use floating-point coordinates after aggregation.

The [Phase 07 economic and evaluation record](../docs/05_ml/phase07_clv_economic_definition_and_validation.md)
defines the approved six-month billed-value proxy and frozen experiment.
[Predictive models and validation](04_clv_modelling/08_clv_predictive_models_and_validation.ipynb)
loads the checksum-verified design and results from
`data/processed/phase07-clv-research/`. Notebook 07 also displays the fitted
baseline when the report is present. Set `NCI_CLV_WORKSPACE` to an absolute local
workspace path if needed. Both render without fitting.

Use `python -m nowa_customer_intelligence.models.clv.research` to generate the
initial evidence in a new local workspace. The archived reference reserve has
already been scored. Use its saved report for review and preserve its frozen
selection. Keep reports, model binaries and executed notebooks outside Git.

## Phase 08 customer segmentation

[Notebook 09](05_customer_segmentation/09_rfm_and_customer_profiling.ipynb)
profiles historical finance, contracts, usage availability and frozen RFM.
[Notebook 10](05_customer_segmentation/10_customer_clustering_and_validation.ipynb)
renders the clustering grid, stability and transfer diagnostics. Both use
the Python 3.12 notebook environment above and read checksum-verified JSON.
They reconstruct only the accepted development source for descriptive
views. They do not fit estimators or re-evaluate the reserve. The current
research run recorded no nominee and the seed-83108 reserve is unscored.
The Phase 08 engineering checkpoint records the reconciled 3,000
account-months and the accepted negative nomination result.
[Approved Phase 08 protocol](../docs/05_ml/phase08_segmentation_scope_and_validation.md).

From the repository root, the research entry point is
`python -m nowa_customer_intelligence.models.segmentation.research`.
The default workspace is `data/processed/phase08-segmentation-research/`.
The runner requires a new workspace and retains its pre-fit evidence.
Keep the completed default workspace for review. Pass `--workspace` to a
new ignored directory only for an authorised research run. Set
`NCI_SEGMENTATION_WORKSPACE` in the notebook kernel environment to select
an existing report outside the default folder. If no default workspace is
present, the notebooks still render offline descriptive analyses and
indicate which sections need the verified report.

Keep Registry databases, source exports, reports, binaries and rendered
notebook review copies outside Git. Execute copies in fresh kernels and
leave saved outputs and execution counters cleared in the repository.

## Phase 09 explainable AI

[Notebook 11](06_explainable_ai/11_churn_model_explainability.ipynb) reports
interventional TreeSHAP on the frozen churn classifier in class-1 probability
and log odds. [Notebook 12](06_explainable_ai/12_clv_model_explainability.ipynb)
reports the four-block Shapley game on the final clipped billed-value predictor,
matched-account MAE permutation and supported sensitivity. Both render verified
JSON in a read-only review. Fresh-kernel verification rendered 18 churn
and 23 CLV figures from the cleared sources. The notebooks exercise neither
the frozen estimators nor protected reserves.
[Approved Phase 09 scope and evidence](../docs/05_ml/phase09_explainability_scope_and_validation.md).

Use a separate Python 3.12 environment outside the repository for the research
runner. The compatible audit used NumPy 2.5.4, scikit-learn 1.9.1, pandas 2.3.3,
SciPy 1.18.1, Joblib 1.6.0, SHAP 0.54.1, Numba 0.68.1, Pandera 0.26.1, Pydantic
2.14.3, PyYAML 6.0.3 and openpyxl 3.1.5. Create the isolated environment
where needed, then run from the repository root:

```bash
python3.12 -m venv /tmp/nci-phase09-compat
/tmp/nci-phase09-compat/bin/python -m pip install \
  numpy==2.5.4 scikit-learn==1.9.1 pandas==2.3.3 scipy==1.18.1 joblib==1.6.0 \
  shap==0.54.1 numba==0.68.1 pandera==0.26.1 pydantic==2.14.3 \
  PyYAML==6.0.3 openpyxl==3.1.5
PYTHONPATH=src /tmp/nci-phase09-compat/bin/python \
  -m nowa_customer_intelligence.explainability.research \
  --workspace data/processed/phase09-explainability-review
```

The workspace must be new. The default notebook report directory is
`data/processed/phase09-explainability-research/`. Set `NCI_XAI_WORKSPACE`
to the absolute path of another verified workspace when using an independent
replay. Notebook-only environments can render the reports without SHAP.
Execute fresh-kernel review copies outside Git. Keep their rendered outputs
and the local research files outside repository sources.
