from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd
import pytest

from frankenmsa.augment.ghostfold import GhostFold
from frankenmsa.augment.ghostfold import _build_ghostfold_command
from frankenmsa.augment.ghostfold import _find_ghostfold_output
from frankenmsa.augment.ghostfold import resolve_ghostfold_command


def test_resolve_ghostfold_command_uses_explicit_bin(monkeypatch):
    monkeypatch.setenv("FRANKENMSA_GHOSTFOLD_BIN", "/tmp/custom-ghostfold")
    monkeypatch.delenv("GHOSTFOLD_BIN", raising=False)
    monkeypatch.delenv("FRANKENMSA_GHOSTFOLD_ROOT", raising=False)
    monkeypatch.delenv("GHOSTFOLD_ROOT", raising=False)
    monkeypatch.setattr("frankenmsa.augment.ghostfold.shutil.which", lambda _: None)

    assert resolve_ghostfold_command() == ["/tmp/custom-ghostfold"]


def test_build_ghostfold_command_supports_cli(monkeypatch, tmp_path):
    fasta_path = tmp_path / "query.fasta"
    fasta_path.write_text(">query\nACDE\n")
    monkeypatch.setattr(
        "frankenmsa.augment.ghostfold.resolve_ghostfold_command",
        lambda: ["/usr/local/bin/ghostfold"],
    )

    command = _build_ghostfold_command(fasta_path, "job")

    assert command == [
        "/usr/local/bin/ghostfold",
        "msa",
        "--project-name",
        "job",
        "--fasta-path",
        str(fasta_path),
    ]


def test_build_ghostfold_command_supports_legacy_script(monkeypatch, tmp_path):
    fasta_path = tmp_path / "query.fasta"
    fasta_path.write_text(">query\nACDE\n")
    monkeypatch.setattr(
        "frankenmsa.augment.ghostfold.resolve_ghostfold_command",
        lambda: ["/opt/ghostfold/ghostfold.sh"],
    )

    command = _build_ghostfold_command(fasta_path, "job")

    assert command == [
        "/opt/ghostfold/ghostfold.sh",
        "--project_name",
        "job",
        "--fasta_file",
        str(fasta_path),
        "--msa-only",
    ]


def test_find_ghostfold_output_prefers_a3m(tmp_path):
    project_dir = tmp_path / "ghostfold_output"
    msa_dir = project_dir / "msa" / "GhostFold_input"
    msa_dir.mkdir(parents=True)
    fasta_path = msa_dir / "pstMSA.fasta"
    fasta_path.write_text(">GhostFold_input\nACDE\n")
    a3m_path = msa_dir / "pstMSA.a3m"
    a3m_path.write_text(">GhostFold_input\nACDE\n")

    assert _find_ghostfold_output(project_dir) == a3m_path


def test_augment_runs_ghostfold_and_reads_output(monkeypatch):
    recorded = {}

    monkeypatch.setattr(
        "frankenmsa.augment.ghostfold.resolve_ghostfold_command",
        lambda: ["ghostfold"],
    )

    def fake_run(command, cwd, capture_output, text):
        recorded["command"] = command
        recorded["cwd"] = cwd

        output_dir = Path(cwd) / "ghostfold_output" / "msa" / "GhostFold_input"
        output_dir.mkdir(parents=True)
        (output_dir / "pstMSA.a3m").write_text(">GhostFold_input\nACDE\n>hit1\nAcDE\n")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("frankenmsa.augment.ghostfold.subprocess.run", fake_run)

    result = GhostFold().augment("ACDE")

    assert isinstance(result, pd.DataFrame)
    assert result["header"].tolist() == ["GhostFold_input", "hit1"]
    assert result["sequence"].tolist() == ["ACDE", "AcDE"]
    assert recorded["command"][:4] == [
        "ghostfold",
        "msa",
        "--project-name",
        "ghostfold_output",
    ]
    assert Path(recorded["cwd"]).name.startswith("frankenmsa-ghostfold-")


def test_augment_raises_when_ghostfold_fails(monkeypatch):
    monkeypatch.setattr(
        "frankenmsa.augment.ghostfold.resolve_ghostfold_command",
        lambda: ["ghostfold"],
    )

    def fake_run(command, cwd, capture_output, text):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="boom")

    monkeypatch.setattr("frankenmsa.augment.ghostfold.subprocess.run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        GhostFold().augment("ACDE")
