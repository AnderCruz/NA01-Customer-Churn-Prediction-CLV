"""Execute cleared Phase 08 notebook sources without model fitting."""

import ast
from pathlib import Path

import pytest

NOTEBOOKS = Path(__file__).resolve().parents[2] / "notebooks/05_customer_segmentation"


@pytest.mark.parametrize(
    ("filename", "evidence"),
    [
        ("09_rfm_and_customer_profiling.ipynb", "£837,747.60"),
        ("10_customer_clustering_and_validation.ipynb", "unique exact RFM tuples"),
    ],
)
def test_descriptive_segmentation_notebook_runs(
    filename: str, evidence: str, tmp_path, monkeypatch
) -> None:
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path))
    notebook = nbformat.read(NOTEBOOKS / filename, as_version=4)
    nbformat.validate(notebook)
    code = [cell for cell in notebook.cells if cell.cell_type == "code"]
    for cell in code:
        assert not cell.outputs and cell.execution_count is None
        methods = {
            node.attr
            for node in ast.walk(ast.parse(cell.source))
            if isinstance(node, ast.Attribute)
        }
        assert methods.isdisjoint(
            {"fit", "fit_transform", "fit_predict", "predict", "predict_proba"}
        )

    nbclient.NotebookClient(
        notebook,
        kernel_name="python3",
        timeout=100,
        resources={"metadata": {"path": str(NOTEBOOKS)}},
    ).execute()
    assert all(cell.execution_count is not None for cell in code)
    rich = [output.get("data", {}) for cell in code for output in cell.outputs]
    assert any("image/png" in data for data in rich)
    assert any(
        evidence in data.get(mime, "") for data in rich for mime in data if mime.startswith("text/")
    )
