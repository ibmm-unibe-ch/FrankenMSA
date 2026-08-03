from __future__ import annotations

import gc
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..runtime import log_message

from .protein_mpnn_support import resolve_proteinmpnn_out_dir
from .protein_mpnn_support import resolve_proteinmpnn_root
from .protein_mpnn_support import resolve_proteinmpnn_weights

_INSTALLER_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "installers"
    / "install_proteinmpnn.py"
)

__all__ = [
    "clean_proteinmpnn_workspace",
    "download_pdb_by_code",
    "fasta_to_a3m",
    "merge_outputs_to_fasta",
    "provision_proteinmpnn",
    "read_text_safe",
    "run_proteinmpnn",
    "split_chain_list",
    "split_fasta_by_chain_separator",
    "write_chain_jsonl",
    "zip_outputs",
]


def split_chain_list(csv_value: str) -> List[str]:
    csv_value = (csv_value or "").strip()
    if not csv_value:
        return []
    parts = [part.strip().upper() for part in csv_value.replace(";", ",").split(",")]
    return [part for part in parts if part and len(part) == 1 and part.isalpha()]


def write_chain_jsonl(
    out_dir: str | Path,
    pdb_path: str | Path,
    designed: List[str],
    fixed: List[str],
) -> Optional[str]:
    if not (designed or fixed):
        return None

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": Path(pdb_path).stem,
        "design_chain_list": designed,
        "fixed_chain_list": fixed,
    }
    jsonl_path = out_dir / "chain_id.jsonl"
    jsonl_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return str(jsonl_path)


def merge_outputs_to_fasta(out_dir: str | Path, stem: str) -> Tuple[str, int]:
    out_dir = Path(out_dir)
    fasta_path = out_dir / f"{stem}_proteinmpnn.fasta"
    count = 0
    with fasta_path.open("w", encoding="utf-8") as fout:
        for filename in sorted(
            glob.glob(os.path.join(out_dir, "**", "*.fa*"), recursive=True)
        ):
            with open(filename, encoding="utf-8", errors="ignore") as fin:
                for line in fin:
                    if line.startswith(">"):
                        count += 1
                        fout.write(f">sample_{count}\n")
                    else:
                        fout.write(line.strip() + "\n")
    return str(fasta_path), count


def fasta_to_a3m(fasta_path: str | Path) -> str:
    fasta_path = Path(fasta_path)
    a3m_path = fasta_path.with_suffix(".a3m")
    with fasta_path.open(encoding="utf-8", errors="ignore") as fin, a3m_path.open(
        "w", encoding="utf-8"
    ) as fout:
        idx = 0
        for line in fin:
            if line.startswith(">"):
                idx += 1
                fout.write(f">sample_{idx}\n")
            else:
                fout.write(line.strip() + "\n")
    return str(a3m_path)


def zip_outputs(
    out_dir: str | Path,
    base: str,
    destination: Optional[str | Path] = None,
) -> str:
    out_dir = Path(out_dir)
    dest_dir = Path(destination).expanduser() if destination else out_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / f"{base}_proteinmpnn_outputs.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in glob.glob(os.path.join(out_dir, "**", "*"), recursive=True):
            if os.path.isfile(filename):
                archive.write(filename, arcname=os.path.relpath(filename, out_dir))
    return str(zip_path)


def read_text_safe(path: str | Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return Path(path).read_text(errors="ignore")


def split_fasta_by_chain_separator(
    full_fasta_path: str | Path,
    out_dir: str | Path,
    base_name: str,
    chain_labels: Optional[List[str]] = None,
) -> Dict[str, str]:
    split_results = {}
    full_fasta_path = Path(full_fasta_path)
    out_dir = Path(out_dir)

    lines = full_fasta_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not lines:
        return {}

    sample_seq = ""
    for line in lines:
        if not line.startswith(">"):
            sample_seq = line.strip()
            break

    if "/" not in sample_seq:
        return {}

    segments = sample_seq.split("/")
    chain_count = len(segments)
    if chain_labels is not None and len(chain_labels) == chain_count:
        labels = list(chain_labels)
    else:
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        labels = [alphabet[idx] if idx < 26 else str(idx) for idx in range(chain_count)]

    chain_files = {}
    try:
        for idx, chain_id in enumerate(labels):
            fasta_path = out_dir / f"{base_name}_chain{chain_id}.fasta"
            chain_files[idx] = {
                "path": fasta_path,
                "handle": fasta_path.open("w", encoding="utf-8"),
                "id": chain_id,
            }

        current_header = None
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                current_header = line
                continue

            parts = line.split("/")
            if len(parts) != chain_count:
                continue
            for idx, seq_part in enumerate(parts):
                chain_file = chain_files[idx]
                chain_file["handle"].write(
                    f"{current_header}_chain{chain_file['id']}\n{seq_part}\n"
                )

        for chain_file in chain_files.values():
            chain_file["handle"].close()
            a3m_path = fasta_to_a3m(chain_file["path"])
            split_results[f"{base_name}_chain{chain_file['id']}"] = read_text_safe(
                a3m_path
            )
    finally:
        for chain_file in chain_files.values():
            handle = chain_file["handle"]
            if not handle.closed:
                handle.close()

    return split_results


def clean_proteinmpnn_workspace(
    root: str | Path = None,
    content_root: str | Path = None,
) -> None:
    if root is None:
        root = os.environ.get("FRANKENMSA_PROTEINMPNN_ROOT", "/content/ProteinMPNN")
    if content_root is None:
        content_root = os.environ.get("FRANKENMSA_CONTENT_ROOT", str(Path(root).parent))
    root = Path(root)
    content_root = Path(content_root)
    try:
        if (root / "outputs_run").is_dir():
            shutil.rmtree(root / "outputs_run", ignore_errors=True)
        for pattern in ("*.pdb", "*.zip", "*.fa", "*.fasta", "*.a3m"):
            for file_path in content_root.glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
    finally:
        gc.collect()


def download_pdb_by_code(
    code: str,
    target_dir: Optional[str | Path] = None,
    tries: int = 3,
    sleep_sec: float = 1.5,
) -> str:
    code = (code or "").strip().upper()
    if not code:
        raise RuntimeError("No PDB code provided.")

    target_dir = (
        Path(target_dir).expanduser()
        if target_dir is not None
        else Path.home() / ".frankenmsa" / "pdb_cache"
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    outfile = target_dir / f"{code}.pdb"
    if _download_with_retries(
        f"https://files.rcsb.org/download/{code}.pdb",
        outfile,
        tries=tries,
        sleep_sec=sleep_sec,
    ):
        return str(outfile)
    if _download_with_retries(
        f"https://files.rcsb.org/view/{code}.pdb",
        outfile,
        tries=tries,
        sleep_sec=sleep_sec,
    ):
        return str(outfile)
    raise RuntimeError(f"Failed to download PDB for code: {code}")


def provision_proteinmpnn(
    root: str = None,
    install_python_deps: bool = True,
) -> Dict[str, str]:
    if root is None:
        root = os.environ.get("FRANKENMSA_PROTEINMPNN_ROOT", "/content/ProteinMPNN")
    if not _INSTALLER_SCRIPT.is_file():
        raise RuntimeError(
            f"ProteinMPNN installer script not found: {_INSTALLER_SCRIPT}"
        )

    install_cmd = [sys.executable, str(_INSTALLER_SCRIPT), "--root", root]
    if install_python_deps:
        install_cmd.append("--install-python-deps")
    subprocess.run(install_cmd, check=True)

    resolved_root = resolve_proteinmpnn_root(root)
    return {
        "root": str(resolved_root),
        "weights_vanilla": str(resolve_proteinmpnn_weights(resolved_root)),
        "weights_soluble": str(
            resolve_proteinmpnn_weights(resolved_root, use_soluble_model=True)
        ),
        "weights_ca": str(resolve_proteinmpnn_weights(resolved_root, ca_only=True)),
        "out_dir": str(
            resolve_proteinmpnn_out_dir(resolved_root, default_name="outputs_run")
        ),
    }


def run_proteinmpnn(
    sampling_temp: float = 1.0,
    num_seqs: int = 128,
    pdb_code: str = "",
    design_chains: str = "",
    fixed_chains: str = "",
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
    runtime: str = "local",
) -> Dict:
    runtime_settings = _resolve_runtime_settings(runtime, proteinmpnn_root)
    log_message(f"ProteinMPNN Runtime settings: {runtime_settings}")
    if clean_workspace and runtime_settings["cleanup_root"] is not None:
        clean_proteinmpnn_workspace(
            root=runtime_settings["cleanup_root"],
            content_root=runtime_settings["content_root"],
        )

    local_pdb, input_mode = _pick_pdb_input(
        pdb_code=(pdb_code or "").strip().upper(),
        uploaded_path=(pdb_path or "").strip(),
        allow_upload=allow_upload,
        download_target_dir=runtime_settings["download_dir"],
    )

    if runtime_settings["provision"]:
        provision_proteinmpnn(
            root=str(runtime_settings["repo_root"]),
            install_python_deps=runtime_settings["install_python_deps"],
        )

    repo_root = resolve_proteinmpnn_root(str(runtime_settings["repo_root"]))
    out_dir = resolve_proteinmpnn_out_dir(
        repo_root, default_name=runtime_settings["out_dir_name"]
    )
    weights_root = resolve_proteinmpnn_weights(
        repo_root,
        use_soluble_model=use_soluble_model,
        ca_only=ca_only,
        override_dir=weights_dir,
    )
    staged_pdb = _stage_pdb(local_pdb, repo_root, out_dir)

    designed_list = split_chain_list(design_chains)
    fixed_list = split_chain_list(fixed_chains)
    jsonl_parsed, jsonl_assigned, use_jsonl_mode = _prepare_chain_inputs(
        repo_root=repo_root,
        out_dir=out_dir,
        pdb_path=staged_pdb,
        design_chains=designed_list,
        fixed_chains=fixed_list,
        homomer=homomer,
    )

    cmd = _build_proteinmpnn_command(
        repo_root=repo_root,
        out_dir=out_dir,
        model_name=model_name,
        weights_root=weights_root,
        num_seqs=num_seqs,
        sampling_temp=sampling_temp,
        use_soluble_model=use_soluble_model,
        ca_only=ca_only,
        staged_pdb=staged_pdb,
        use_jsonl_mode=use_jsonl_mode,
        jsonl_parsed=jsonl_parsed,
        jsonl_assigned=jsonl_assigned,
        homomer=homomer,
        designed_list=designed_list,
        fixed_list=fixed_list,
    )

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
    split_chains = split_fasta_by_chain_separator(
        full_fasta_path=fasta_path,
        out_dir=out_dir,
        base_name=pdb_stem,
        chain_labels=designed_list if designed_list else None,
    )
    zip_path = zip_outputs(
        out_dir, base=pdb_stem, destination=runtime_settings["zip_destination"]
    )

    if auto_download and runtime == "colab":
        try:
            from google.colab import files

            files.download(zip_path)
        except Exception:
            pass

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
        "split_chains": split_chains,
    }


def _resolve_runtime_settings(
    runtime: str, proteinmpnn_root: Optional[str]
) -> Dict[str, object]:
    runtime = (runtime or "local").strip().lower()
    if runtime == "colab":
        repo_root = Path(proteinmpnn_root or os.environ.get("FRANKENMSA_PROTEINMPNN_ROOT", "/content/ProteinMPNN"))
        return {
            "provision": not (repo_root.is_dir() and (repo_root / "protein_mpnn_run.py").is_file()),
            "install_python_deps": True,
            "repo_root": repo_root,
            "out_dir_name": "outputs_run",
            "zip_destination": "/content",
            "download_dir": Path("/content"),
            "cleanup_root": repo_root,
            "content_root": Path("/content"),
        }
    if runtime == "local":
        repo_root = (
            Path(proteinmpnn_root)
            if proteinmpnn_root
            else resolve_proteinmpnn_root(None)
        )
        return {
            "provision": False,
            "install_python_deps": False,
            "repo_root": repo_root,
            "out_dir_name": "outputs_local",
            "zip_destination": None,
            "download_dir": Path.home() / ".frankenmsa" / "pdb_cache",
            "cleanup_root": None,
            "content_root": None,
        }
    raise ValueError(f"Unsupported runtime: {runtime}")


def _pick_pdb_input(
    pdb_code: str,
    uploaded_path: str,
    allow_upload: bool,
    download_target_dir: Path,
) -> Tuple[str, str]:
    if uploaded_path:
        if not os.path.isfile(uploaded_path):
            raise RuntimeError(f"Uploaded pdb_path not found: {uploaded_path}")
        return uploaded_path, "uploaded_file"
    if pdb_code:
        return (
            download_pdb_by_code(pdb_code, target_dir=download_target_dir),
            "pdb_code",
        )
    if allow_upload:
        raise RuntimeError(
            "Interactive upload is not supported from the library workflow. Provide pdb_path from the UI instead."
        )
    raise RuntimeError(
        "Please provide a PDB code or upload a PDB/CIF file via the UI before running ProteinMPNN."
    )


def _prepare_chain_inputs(
    repo_root: Path,
    out_dir: Path,
    pdb_path: Path,
    design_chains: List[str],
    fixed_chains: List[str],
    homomer: bool,
) -> Tuple[Optional[str], Optional[str], bool]:
    if homomer:
        return None, None, False

    helper_parse = repo_root / "helper_scripts" / "parse_multiple_chains.py"
    helper_assign = repo_root / "helper_scripts" / "assign_fixed_chains.py"
    jsonl_parsed = out_dir / "parsed_pdbs.jsonl"
    jsonl_assigned = out_dir / "assigned_pdbs.jsonl"

    if helper_parse.is_file() and helper_assign.is_file():
        temp_pdb_dir = out_dir / "temp_pdbs"
        temp_pdb_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdb_path, temp_pdb_dir / pdb_path.name)
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(helper_parse),
                    f"--input_path={temp_pdb_dir}",
                    f"--output_path={jsonl_parsed}",
                ],
                check=True,
            )
            if design_chains:
                subprocess.run(
                    [
                        sys.executable,
                        str(helper_assign),
                        f"--input_path={jsonl_parsed}",
                        f"--output_path={jsonl_assigned}",
                        "--chain_list",
                        " ".join(design_chains),
                    ],
                    check=True,
                )
                return str(jsonl_parsed), str(jsonl_assigned), True
        except Exception:
            pass

    chain_jsonl = write_chain_jsonl(out_dir, pdb_path, design_chains, fixed_chains)
    if chain_jsonl is None:
        return None, None, False
    return None, chain_jsonl, False


def _build_proteinmpnn_command(
    repo_root: Path,
    out_dir: Path,
    model_name: str,
    weights_root: Path,
    num_seqs: int,
    sampling_temp: float,
    use_soluble_model: bool,
    ca_only: bool,
    staged_pdb: Path,
    use_jsonl_mode: bool,
    jsonl_parsed: Optional[str],
    jsonl_assigned: Optional[str],
    homomer: bool,
    designed_list: List[str],
    fixed_list: List[str],
) -> List[str]:
    cmd = [
        sys.executable,
        str(repo_root / "protein_mpnn_run.py"),
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
        "--batch_size",
        "1",
    ]
    if use_soluble_model:
        cmd.append("--use_soluble_model")
    if ca_only:
        cmd.append("--ca_only")

    if use_jsonl_mode and jsonl_parsed and jsonl_assigned:
        cmd.extend(["--jsonl_path", jsonl_parsed, "--chain_id_jsonl", jsonl_assigned])
        return cmd

    cmd.extend(["--pdb_path", str(staged_pdb)])
    if not homomer:
        chain_jsonl = jsonl_assigned or write_chain_jsonl(
            out_dir, staged_pdb, designed_list, fixed_list
        )
        if chain_jsonl:
            cmd.extend(["--chain_id_jsonl", chain_jsonl])
    return cmd


def _download_with_retries(
    url: str,
    out_path: Path,
    tries: int = 3,
    sleep_sec: float = 1.5,
) -> bool:
    request = urllib.request.Request(str(url), headers={"User-Agent": "Mozilla/5.0"})
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


def _stage_pdb(local_pdb: str, repo_root: Path, out_dir: Path) -> Path:
    source = Path(local_pdb).expanduser().resolve()
    repo_copy = repo_root / source.name
    out_copy = out_dir / source.name
    if not _same_file(source, repo_copy):
        shutil.copy2(source, repo_copy)
    if not _same_file(repo_copy, out_copy):
        shutil.copy2(repo_copy, out_copy)
    return repo_copy


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
