# proteinmpnn_runner.py
# A compact, Colab-friendly runner that wraps your 4-cell workflow into one module.
# - Parses params (URL or query string)
# - Gets PDB (download or optional upload)
# - Sets up ProteinMPNN repo & deps
# - Runs ProteinMPNN
# - Merges FASTA, writes minimal A3M, zips outputs
# - Returns a summary dict
#
# Comments in English as requested.

import gc
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

from helpers.proteinmpnn_common import (
    fasta_to_a3m,
    merge_outputs_to_fasta,
    read_text_safe,
    split_chain_list,
    write_chain_jsonl,
    zip_outputs,
)

# ---------- Utilities ----------


def _print_json(title: str, obj):
    print(title)
    print(json.dumps(obj, indent=2))
    print("-" * 60)


# ---------- Workspace & PDB ----------


def clean_colab_workspace():
    """Lightweight cleanup for repeatable runs."""
    print("🧹 Cleaning workspace... ", end="", flush=True)
    try:
        os.system("rm -rf /content/ProteinMPNN/outputs_run/* 2>/dev/null")
        os.system("find /content -maxdepth 2 -type f -name '*.pdb' -delete 2>/dev/null")
        os.system(
            "rm -f /content/*.zip /content/*.fa /content/*.fasta /content/*.a3m 2>/dev/null"
        )
    except Exception:
        pass
    gc.collect()
    print("done.")


def _download_with_retries(
    url: str, out_path: str, tries: int = 4, sleep_sec: float = 1.5
) -> bool:
    """Robust downloader (urllib with simple retries) for Colab."""
    import urllib.request, urllib.error, time

    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    for i in range(1, tries + 1):
        try:
            print(f"🌐 [urllib] {url} (try {i}/{tries})...")
            with urllib.request.urlopen(req, timeout=20) as r, open(
                out_path, "wb"
            ) as f:
                f.write(r.read())
            return True
        except urllib.error.HTTPError as e:
            print(f"  ↺ urllib retry because: HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            print(f"  ↺ urllib retry because: {e}")
        time.sleep(sleep_sec)
    return False


def get_pdb_file(pdb_code: str, allow_upload: bool = True) -> str:
    """
    If pdb_code is provided: download from RCSB.
    Else if allow_upload and in Colab: ask user to upload.
    Returns the local PDB filepath; raises on failure.
    """
    if pdb_code:
        fn = f"{pdb_code}.pdb"
        # Try /download then /view
        if _download_with_retries(
            f"https://files.rcsb.org/download/{fn}", fn
        ) or _download_with_retries(f"https://files.rcsb.org/view/{fn}", fn):
            print(f"✅ Downloaded PDB to {fn}")
            return fn
        raise RuntimeError(f"Failed to download PDB for code: {pdb_code}")

    if allow_upload:
        # Only attempt Colab upload when running in a real Colab front-end session.
        try:
            from google.colab import files  # type: ignore

            try:
                from IPython import get_ipython  # type: ignore

                ip = get_ipython()
                has_kernel = bool(ip and getattr(ip, "kernel", None))
            except Exception:
                has_kernel = False
            if not has_kernel:
                raise RuntimeError(
                    "Colab upload UI is not available in this environment. Please use the web UI upload (pdb_path) or provide a PDB code."
                )

            print("📤 No PDB code provided. Please upload your local .pdb file:")
            uploaded = files.upload()
            if not uploaded:
                raise RuntimeError("No file uploaded.")
            name = list(uploaded.keys())[0]
            print(f"✅ Uploaded: {name}")
            return name
        except Exception as e:
            raise RuntimeError(
                f"Upload failed (no Colab front-end?): {e}. Please use the web UI upload (pdb_path) or provide a PDB code."
            )

    raise RuntimeError("No PDB code provided and uploads are disabled.")


# ---------- ProteinMPNN setup & run ----------


def ensure_proteinmpnn(root: str = "/content/ProteinMPNN") -> Dict:
    """
    Clone ProteinMPNN if missing; install deps; detect weights paths; return env info.
    """
    if not os.path.isdir(root):
        print("📥 Cloning ProteinMPNN...")
        subprocess.run(
            ["git", "clone", "-q", "https://github.com/dauparas/ProteinMPNN.git", root],
            check=True,
        )

    print("📦 Installing Python deps (quiet)...")
    # Pin biopython==1.83 and einops==0.7.0 for reproducibility
    subprocess.run(
        ["pip", "install", "-q", "biopython==1.83", "einops==0.7.0"], check=True
    )

    # Weights location (these folders are part of the repo)
    vanilla = os.path.join(root, "vanilla_model_weights")
    soluble = os.path.join(root, "soluble_model_weights")
    ca = os.path.join(root, "ca_model_weights")

    env = {
        "root": root,
        "weights": {"vanilla": vanilla, "soluble": soluble, "ca": ca},
        "out_dir": os.path.join(root, "outputs_run"),
        "cuda_available": _cuda_available(),
    }
    os.makedirs(env["out_dir"], exist_ok=True)

    weights_ready = {k: os.path.isdir(v) for k, v in env["weights"].items()}
    if not all(weights_ready.values()):
        # Try to fetch weights if any folder is missing
        fetched = _ensure_model_weights(root)
        weights_ready = fetched

    _print_json(
        "=== Environment summary ===",
        {
            "repo_root": env["root"],
            "weights_ready": weights_ready,
            "out_dir": env["out_dir"],
            "cuda_available": env["cuda_available"],
        },
    )
    return env


def _cuda_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _ensure_model_weights(root: str) -> Dict[str, bool]:
    """
    Best-effort: make sure weight folders exist by trying git LFS and the repo's helper script.
    Returns a dict of {vanilla|soluble|ca: bool} after attempts.
    """
    vanilla = os.path.join(root, "vanilla_model_weights")
    soluble = os.path.join(root, "soluble_model_weights")
    ca = os.path.join(root, "ca_model_weights")

    def _exists() -> Dict[str, bool]:
        return {
            "vanilla": os.path.isdir(vanilla),
            "soluble": os.path.isdir(soluble),
            "ca": os.path.isdir(ca),
        }

    ready = _exists()
    if all(ready.values()):
        return ready

    try:
        subprocess.run(
            ["git", "-C", root, "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:

        try:
            shutil.rmtree(root, ignore_errors=True)
        except Exception:
            pass
        subprocess.run(
            ["git", "clone", "-q", "https://github.com/dauparas/ProteinMPNN.git", root],
            check=True,
        )

    try:
        subprocess.run(
            ["git", "-C", root, "lfs", "install"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        subprocess.run(
            ["git", "-C", root, "lfs", "fetch", "--all"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        subprocess.run(
            ["git", "-C", root, "lfs", "pull"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        subprocess.run(
            ["git", "-C", root, "lfs", "checkout"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        pass

    if not all(_exists().values()):
        helper = os.path.join(root, "get_model_weights.sh")
        if os.path.isfile(helper):
            try:
                subprocess.run(
                    ["bash", helper],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            except Exception:
                pass

    ready = _exists()
    try:

        print(
            ">> weights present:",
            [p for p in [vanilla, soluble, ca] if os.path.isdir(p)],
        )
        subprocess.run(
            ["bash", "-lc", f"du -h --max-depth=1 {root} | sort -h"], check=False
        )
    except Exception:
        pass

    return ready


def resolve_weights(env: Dict, use_soluble_model: bool, ca_only: bool) -> str:
    if ca_only:
        w = env["weights"]["ca"]
    elif use_soluble_model:
        w = env["weights"]["soluble"]
    else:
        w = env["weights"]["vanilla"]
    if not os.path.isdir(w):
        # One more best-effort attempt to fetch
        ready = _ensure_model_weights(env["root"])
        if not os.path.isdir(w):
            raise RuntimeError(
                f"Model weights folder not found: {w}\n"
                f"weights_ready={ready}. "
                f"If cloning via git, ensure git-lfs is installed/enabled, "
                f"or run get_model_weights.sh inside {env['root']}."
            )
    return w


def run_proteinmpnn(
    sampling_temp: float = 1.0,
    num_seqs: int = 128,
    pdb_code: str = "",
    design_csv: str = "",
    fixed_csv: str = "",
    homomer: bool = True,  # currently for info only; ProteinMPNN JSONL ties can be added later if needed
    model_name: str = "v_48_020",
    use_soluble_model: bool = False,
    ca_only: bool = False,
    allow_upload: bool = True,  # only applies on Colab
    clean_workspace: bool = False,  # wipe old outputs each run
    auto_download: bool = False,  # auto-download ZIP in Colab
    pdb_path: str = "",
) -> Dict:
    """
    Main entry point: does the whole workflow and returns a summary dict.
    """
    if clean_workspace:
        clean_colab_workspace()

    # 1) PDB input (prefer explicit local path from Dash upload)
    code = (pdb_code or "").strip().upper()
    uploaded_path = (pdb_path or "").strip()
    print(
        f"[Runner] incoming: code='{code}' uploaded_path='{uploaded_path}' allow_upload={allow_upload}"
    )

    local_pdb = ""
    input_mode = ""

    if uploaded_path:
        if os.path.isfile(uploaded_path):
            local_pdb = uploaded_path
            input_mode = "uploaded_file"
            print(f"[Runner] Using uploaded file: {local_pdb}")
        else:
            raise RuntimeError(f"Uploaded pdb_path not found: {uploaded_path}")
    elif code:
        local_pdb = get_pdb_file(code, allow_upload=allow_upload)
        input_mode = "pdb_code"
    else:
        if allow_upload:
            # Fallback to Colab-side interactive upload only when explicitly allowed
            local_pdb = get_pdb_file("", allow_upload=True)
            input_mode = "colab_upload"
        else:
            raise RuntimeError(
                "No PDB code or uploaded file provided (and uploads are disabled)."
            )

    # 2) Setup env
    env = ensure_proteinmpnn()
    root = env["root"]
    out_dir = env["out_dir"]
    weights_root = resolve_weights(env, use_soluble_model, ca_only)

    # Stage PDB into the repo root (and also into out_dir) because ProteinMPNN may change cwd internally
    import shutil

    pdb_basename = os.path.basename(local_pdb)
    staged_pdb_root = os.path.join(root, pdb_basename)
    staged_pdb_out = os.path.join(out_dir, pdb_basename)

    if os.path.abspath(local_pdb) != os.path.abspath(staged_pdb_root):
        shutil.copy2(local_pdb, staged_pdb_root)

    # Also copy to out_dir to be safe if the runner changes cwd (best-effort)
    try:
        os.makedirs(out_dir, exist_ok=True)
        if not os.path.isfile(staged_pdb_out):
            shutil.copy2(staged_pdb_root, staged_pdb_out)
    except Exception as e:
        print(
            f"\n⚠️ Could not copy PDB into out_dir '{out_dir}': {e}\nProceeding anyway; runner will use --pdb_path={staged_pdb_root}."
        )

    if not os.path.isfile(staged_pdb_root):
        raise RuntimeError(
            f"Staged PDB not found at {staged_pdb_root}. Original local_pdb={local_pdb}"
        )

    # Use absolute path when calling the runner (even if the script normalizes to basename)
    pdb_arg_abs = os.path.abspath(staged_pdb_root)

    # 3) Prepare chain controls
    designed_list = split_chain_list(design_csv)
    fixed_list = split_chain_list(fixed_csv)
    chain_jsonl = write_chain_jsonl(out_dir, local_pdb, designed_list, fixed_list)

    # 4) Build command
    cmd = [
        _py_exe(),
        f"{root}/protein_mpnn_run.py",
        "--pdb_path",
        pdb_arg_abs,
        "--out_folder",
        out_dir,
        "--model_name",
        model_name,
        "--path_to_model_weights",
        weights_root,
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

    # 5) Execute
    print("🔧 Command:\n ", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    print("=== STDOUT ===\n", proc.stdout[:2000])
    print("\n=== STDERR ===\n", proc.stderr[:2000])

    if proc.returncode != 0:
        raise RuntimeError("ProteinMPNN run failed. See logs above.")

    # 6) Merge outputs -> FASTA
    fasta_out, n = merge_outputs_to_fasta(out_dir, Path(local_pdb).stem)
    print(f"✅ Merged FASTA: {fasta_out} (N={n} sequences)")

    # 7) Minimal A3M
    a3m_out = fasta_to_a3m(fasta_out)
    print(f"✅ Minimal A3M: {a3m_out}")

    # Expose A3M to the web UI: capture filename and contents so the frontend
    # can inject it into the file selector without changing the download flow.
    a3m_path_obj = Path(a3m_out)
    a3m_name = a3m_path_obj.name  # ensures the returned name includes the .a3m suffix
    a3m_text = read_text_safe(a3m_path_obj)

    # 8) Zip outputs (FASTA + A3M + raw)
    zip_path = zip_outputs(out_dir, base=Path(local_pdb).stem, destination="/content")
    print(f"🗜️  Zipped outputs: {zip_path}")

    # Optional auto-download in Colab
    if auto_download:
        try:
            from google.colab import files as colab_files  # type: ignore

            colab_files.download(zip_path)
        except Exception as e:
            print(f"⚠️ Auto-download failed: {e}. You can manually download: {zip_path}")

    return {
        "pdb_path": local_pdb,
        "out_dir": out_dir,
        "fasta": fasta_out,
        "a3m": a3m_out,
        "zip": zip_path,
        "num_sequences": n,
        "cuda_available": env["cuda_available"],
        "weights_root": weights_root,
        "model_name": model_name,
        "designed_chains": designed_list or "ALL",
        "fixed_chains": fixed_list or "NONE",
        "homomer": homomer,
        "sampling_temp": float(sampling_temp),
        "num_seqs": int(num_seqs),
        "input_mode": input_mode,
        "a3m_path": a3m_out,
        "a3m_name": a3m_name,
        "a3m_text": a3m_text,
    }


def _py_exe() -> str:
    return os.environ.get("PYTHON", "python3")
