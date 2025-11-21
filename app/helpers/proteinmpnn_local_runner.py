"""Local ProteinMPNN runner used when FrankenMSA runs outside Google Colab.

Environment variables:
    PROTEINMPNN_LOCAL_ROOT  -> absolute path to an existing ProteinMPNN checkout
    PROTEINMPNN_OUT_DIR     -> optional override for the output directory
    PROTEINMPNN_WEIGHTS_DIR -> absolute path to the weight folder to pass directly
    PROTEINMPNN_WEIGHTS_ROOT-> folder that contains the vanilla/soluble/ca weight subdirs
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

from helpers.proteinmpnn_common import (
    fasta_to_a3m,
    merge_outputs_to_fasta,
    read_text_safe,
    split_chain_list,
    write_chain_jsonl,
    zip_outputs,
)

_DEFAULT_REPO = Path(__file__).resolve().parents[2] / "ProteinMPNN"


def run_proteinmpnn(
    sampling_temp: float = 1.0,
    num_seqs: int = 128,
    pdb_code: str = "",
    design_csv: str = "",
    fixed_csv: str = "",
    homomer: bool = True,
    model_name: str = "v_48_020",
    use_soluble_model: bool = False,
    ca_only: bool = False,
    allow_upload: bool = False,
    clean_workspace: bool = False,
    auto_download: bool = False,
    pdb_path: str = "",
    proteinmpnn_root: Optional[str] = None,
    weights_dir: Optional[str] = None,
) -> Dict:
    """Run ProteinMPNN by calling an existing local checkout."""
    code = (pdb_code or "").strip().upper()
    uploaded_path = (pdb_path or "").strip()

    local_pdb, input_mode = _pick_pdb_input(code, uploaded_path, allow_upload)
    repo_root = _resolve_repo_root(proteinmpnn_root)
    out_dir = _resolve_out_dir(repo_root)

    if clean_workspace:
        print(
            "Cleaning up a local ProteinMPNN repo is not possible. Please, delete it manually."
        )

    weights_root = _resolve_weights(repo_root, use_soluble_model, ca_only, weights_dir)

    staged_pdb = _stage_pdb(local_pdb, repo_root, out_dir)

    designed_list = split_chain_list(design_csv)
    fixed_list = split_chain_list(fixed_csv)
    chain_jsonl = write_chain_jsonl(out_dir, staged_pdb, designed_list, fixed_list)

    cmd = [
        _python_executable(),
        str(Path(repo_root) / "protein_mpnn_run.py"),
        "--pdb_path",
        str(staged_pdb),
        "--out_folder",
        str(out_dir),
        "--model_name",
        model_name,
        "--path_to_model_weights",
        str(weights_root),
        "--num_seq_per_target",
        str(int(num_seqs)),
        "--sampling_temp",
        str(float(sampling_temp)),
    ]
    if use_soluble_model:
        cmd.append("--use_soluble_model")
    if ca_only:
        cmd.append("--ca_only")
    if chain_jsonl:
        cmd.extend(["--chain_id_jsonl", chain_jsonl])

    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "ProteinMPNN run failed.\nSTDOUT:\n"
            f"{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )

    pdb_stem = Path(local_pdb).stem
    fasta_path, count = merge_outputs_to_fasta(out_dir, pdb_stem)
    a3m_path = fasta_to_a3m(fasta_path)
    a3m_text = read_text_safe(a3m_path)
    zip_path = zip_outputs(out_dir, base=pdb_stem)

    if auto_download:
        print("⚠️ auto_download is not supported outside Colab; ignoring request.")

    return {
        "pdb_path": local_pdb,
        "out_dir": str(out_dir),
        "fasta": fasta_path,
        "a3m": a3m_path,
        "zip": zip_path,
        "num_sequences": count,
        "cuda_available": _cuda_available(),
        "weights_root": str(weights_root),
        "model_name": model_name,
        "designed_chains": designed_list or "ALL",
        "fixed_chains": fixed_list or "NONE",
        "homomer": homomer,
        "sampling_temp": float(sampling_temp),
        "num_seqs": int(num_seqs),
        "input_mode": input_mode,
        "a3m_path": a3m_path,
        "a3m_name": Path(a3m_path).name,
        "a3m_text": a3m_text,
    }


def _pick_pdb_input(
    code: str, uploaded_path: str, allow_upload: bool
) -> tuple[str, str]:
    if uploaded_path:
        if not os.path.isfile(uploaded_path):
            raise RuntimeError(f"Uploaded pdb_path not found: {uploaded_path}")
        return uploaded_path, "uploaded_file"
    if code:
        return _download_pdb_by_code(code), "pdb_code"
    if allow_upload:
        raise RuntimeError(
            "Local ProteinMPNN runs cannot open the Colab upload dialog. Please use the web UI upload component."
        )
    raise RuntimeError(
        "Please provide a PDB code or upload a PDB/CIF file via the UI before running ProteinMPNN locally."
    )


def _download_pdb_by_code(code: str) -> str:
    target_dir = Path.home() / ".frankenmsa" / "pdb_cache"
    target_dir.mkdir(parents=True, exist_ok=True)
    outfile = target_dir / f"{code}.pdb"
    if _download_with_retries(f"https://files.rcsb.org/download/{code}.pdb", outfile):
        return str(outfile)
    if _download_with_retries(f"https://files.rcsb.org/view/{code}.pdb", outfile):
        return str(outfile)
    raise RuntimeError(f"Failed to download PDB for code: {code}")


def _download_with_retries(
    url: str, out_path: Path, tries: int = 3, sleep_sec: float = 1.5
) -> bool:
    import urllib.request
    import urllib.error
    import time

    headers = {"User-Agent": "Mozilla/5.0"}
    request = urllib.request.Request(str(url), headers=headers)
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(request, timeout=20) as response, out_path.open(
                "wb"
            ) as handle:
                handle.write(response.read())
            return True
        except urllib.error.HTTPError as err:
            print(f"Retry {attempt}/{tries} for {url}: HTTP {err.code} {err.reason}")
        except Exception as exc:
            print(f"Retry {attempt}/{tries} for {url}: {exc}")
        time.sleep(sleep_sec)
    return False


def _resolve_repo_root(custom_root: Optional[str]) -> Path:
    candidates = [
        custom_root,
        os.environ.get("PROTEINMPNN_LOCAL_ROOT"),
        str(_DEFAULT_REPO),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if (path / "protein_mpnn_run.py").is_file():
            return path
    raise RuntimeError(
        "Could not locate a ProteinMPNN checkout. Set PROTEINMPNN_LOCAL_ROOT or pass proteinmpnn_root."
    )


def _resolve_out_dir(repo_root: Path) -> Path:
    override = os.environ.get("PROTEINMPNN_OUT_DIR")
    out_dir = Path(override).expanduser() if override else repo_root / "outputs_local"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _resolve_weights(
    repo_root: Path,
    use_soluble_model: bool,
    ca_only: bool,
    override_dir: Optional[str],
) -> Path:
    direct = override_dir or os.environ.get("PROTEINMPNN_WEIGHTS_DIR")
    if direct:
        direct_path = Path(direct).expanduser()
        if direct_path.is_dir():
            return direct_path
        raise RuntimeError(f"Weights directory not found: {direct_path}")

    base_override = os.environ.get("PROTEINMPNN_WEIGHTS_ROOT")
    base_candidates = [base_override, str(repo_root)]
    subdir = (
        "ca_model_weights"
        if ca_only
        else ("soluble_model_weights" if use_soluble_model else "vanilla_model_weights")
    )

    for candidate in base_candidates:
        if not candidate:
            continue
        candidate_path = Path(candidate).expanduser()
        target = candidate_path / subdir
        if target.is_dir():
            return target

    raise RuntimeError(
        "Unable to locate ProteinMPNN model weights. Set PROTEINMPNN_WEIGHTS_DIR or PROTEINMPNN_WEIGHTS_ROOT."
    )


def _stage_pdb(local_pdb: str, repo_root: Path, out_dir: Path) -> Path:
    source = Path(local_pdb).expanduser().resolve()
    repo_copy = repo_root / source.name
    out_copy = out_dir / source.name

    if not _same_file(source, repo_copy):
        shutil.copy2(source, repo_copy)
    if not _same_file(repo_copy, out_copy):
        shutil.copy2(repo_copy, out_copy)
    return repo_copy


def _python_executable() -> str:
    return os.environ.get("PYTHON", "python3")


def _cuda_available() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except Exception:
        return False


def _same_file(first: Path, second: Path) -> bool:
    try:
        return first.resolve(strict=True) == second.resolve(strict=True)
    except FileNotFoundError:
        return False
