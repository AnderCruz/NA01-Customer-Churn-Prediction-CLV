"""Replay cleared Phase 09 notebooks without training or running explanations."""

import ast
from hashlib import sha256
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOKS = ROOT / "notebooks/06_explainable_ai"


@pytest.mark.parametrize(
    ("name", "filename"),
    [
        ("churn", "11_churn_model_explainability.ipynb"),
        ("clv", "12_clv_model_explainability.ipynb"),
    ],
)
def test_fresh_read_only_notebook_replay(name, filename, tmp_path, monkeypatch) -> None:
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    artifact_home = ROOT / "data/processed/phase09-explainability-research"
    manifest = artifact_home / "manifest.json"
    monkeypatch.delenv("NCI_XAI_WORKSPACE", raising=False)
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path))
    source = NOTEBOOKS / filename
    before_bytes = source.read_bytes()
    book = nbformat.read(source, as_version=4)
    nbformat.validate(book)
    analysed = [(cell.cell_type, cell.source) for cell in book.cells]
    code = [cell for cell in book.cells if cell.cell_type == "code"]
    for cell in code:
        assert cell.execution_count is None and not cell.outputs
        assert not {
            node.attr
            for node in ast.walk(ast.parse(cell.source))
            if isinstance(node, ast.Attribute)
        } & {"fit", "fit_transform", "predict", "predict_proba"}
    paths = [manifest, artifact_home / f"{name}.json", artifact_home / "protocol.json"]
    hashes = [sha256(path.read_bytes()).hexdigest() for path in paths] if manifest.is_file() else []
    nbclient.NotebookClient(
        book, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(NOTEBOOKS)}}
    ).execute()
    assert [(cell.cell_type, cell.source) for cell in book.cells] == analysed
    assert all(cell.execution_count is not None for cell in code)
    assert source.read_bytes() == before_bytes
    rich = [output.get("data", {}) for cell in code for output in cell.outputs]
    if hashes:
        assert sum("image/png" in data for data in rich) >= 12
        assert [sha256(path.read_bytes()).hexdigest() for path in paths] == hashes
        assert any("Primary explanation" in data.get("text/markdown", "") for data in rich)
    else:
        assert any(
            "verified Phase 09 research report is required" in data.get("text/markdown", "")
            for data in rich
        )
