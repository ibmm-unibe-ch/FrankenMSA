from pathlib import Path

from frankenmsa.inverse_fold.protein_mpnn_support import resolve_proteinmpnn_root
from frankenmsa.inverse_fold.protein_mpnn_support import resolve_proteinmpnn_weights


def _make_checkout(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "helper_scripts").mkdir(exist_ok=True)
    (root / "protein_mpnn_run.py").write_text("print('ok')\n")
    return root


def test_resolve_proteinmpnn_root_from_explicit_directory(tmp_path):
    checkout = _make_checkout(tmp_path / "ProteinMPNN")
    resolved = resolve_proteinmpnn_root(str(checkout))
    assert resolved == checkout


def test_resolve_proteinmpnn_root_from_nested_directory(tmp_path):
    checkout = _make_checkout(tmp_path / "workspace" / "ProteinMPNN")
    resolved = resolve_proteinmpnn_root(str(tmp_path / "workspace"))
    assert resolved == checkout


def test_resolve_proteinmpnn_weights_prefers_override_directory(tmp_path):
    checkout = _make_checkout(tmp_path / "ProteinMPNN")
    override = tmp_path / "weights"
    override.mkdir()
    resolved = resolve_proteinmpnn_weights(checkout, override_dir=str(override))
    assert resolved == override


def test_resolve_proteinmpnn_weights_uses_weight_subdirectory(tmp_path):
    checkout = _make_checkout(tmp_path / "ProteinMPNN")
    weight_dir = checkout / "soluble_model_weights"
    weight_dir.mkdir()
    resolved = resolve_proteinmpnn_weights(checkout, use_soluble_model=True)
    assert resolved == weight_dir
