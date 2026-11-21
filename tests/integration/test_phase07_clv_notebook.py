"""Verify the historical CLV notebook against the offline reference reconstruction."""

import ast
from pathlib import Path

import pytest

NOTEBOOK = (
    Path(__file__).resolve().parents[2]
    / "notebooks/04_clv_modelling/07_clv_historical_value_and_baselines.ipynb"
)


def test_historical_value_notebook_runs_in_a_fresh_kernel(tmp_path, monkeypatch) -> None:
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path))
    book = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(book)
    code = [cell for cell in book.cells if cell.cell_type == "code"]
    for cell in code:
        assert cell.execution_count is None and not cell.outputs
        assert not {
            node.attr
            for node in ast.walk(ast.parse(cell.source))
            if isinstance(node, ast.Attribute)
        } & {"fit", "predict", "predict_proba"}
    client = nbclient.NotebookClient(
        book,
        kernel_name="python3",
        timeout=90,
        resources={"metadata": {"path": str(NOTEBOOK.parent)}},
    )
    client.execute()
    rich = [output.get("data", {}) for cell in code for output in cell.outputs]
    assert all(cell.execution_count is not None for cell in code)
    assert any("image/png" in data for data in rich)
    assert any("£1,566,111.80" in data.get("text/markdown", "") for data in rich)


def test_predictive_notebook_executes_from_verified_report(tmp_path, monkeypatch) -> None:
    from hashlib import sha256
    from json import dumps

    from nowa_customer_intelligence.models.clv.research import PROTOCOL, load_report

    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    metrics = {"MAE": 20, "RMSE": 25, "Bias": 4, "Aggregate error": 12, "Median AE": 15}
    date = "2023-01-31T23:59:59+00:00"
    support = {
        name: {"first_observation": date, "last_observation": date, "accounts": 3}
        for name in ("training", "validation", "reserve")
    }
    audit = {"states": {"mature_positive": 2, "mature_zero": 1}, "selection_exclusions": {}}
    design = {
        "support": support,
        "development_audit": audit,
        "reserve_audit": audit,
        "features": [{"name": "tenure_days"}],
        "protocol": PROTOCOL,
        "configurations": {"Training median": {"strategy": "median"}},
    }
    validation = [
        {
            "Actual GBP": actual,
            "Predicted GBP": pred,
            "Observation month": "2023-01",
            "Cadence": "monthly",
            "Historical GBP": 240,
            "Tenure days": 180,
        }
        for actual, pred in ((0, 15), (170, 195), (370, 390))
    ]
    report = {
        "design": design,
        "validation": validation,
        "frozen": {"name": "Training median"},
        "scores": {"Training median": {"training": metrics, "validation": metrics}},
        "reserve": metrics,
        "validation_mae_interval": [12, 29],
        "reserve_mae_interval": [14, 31],
        "feature_quality": {"tenure_days": {"training_missing": 0}},
    }
    (tmp_path / "design.json").write_text(dumps(design))
    results = tmp_path / "results"
    results.mkdir()
    raw = dumps(report).encode()
    (results / "report.json").write_bytes(raw)
    (results / "manifest.json").write_text(dumps({"report_sha256": sha256(raw).hexdigest()}))
    monkeypatch.setenv("NCI_CLV_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path))
    path = NOTEBOOK.with_name("08_clv_predictive_models_and_validation.ipynb")
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    code = [cell for cell in notebook.cells if cell.cell_type == "code"]
    assert all(not cell.outputs and cell.execution_count is None for cell in code)
    assert not any(
        isinstance(node, ast.Attribute) and node.attr in {"fit", "predict", "predict_proba"}
        for cell in code
        for node in ast.walk(ast.parse(cell.source))
    )
    nbclient.NotebookClient(
        notebook,
        kernel_name="python3",
        timeout=90,
        resources={"metadata": {"path": str(path.parent)}},
    ).execute()
    assert any("image/png" in output.get("data", {}) for cell in code for output in cell.outputs)
    assert load_report(tmp_path) == report
    (results / "report.json").write_text("{}")
    with pytest.raises(ValueError, match="integrity failed"):
        load_report(tmp_path)
