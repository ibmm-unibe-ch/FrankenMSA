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


# proteinmpnn_runner.py
# Fixed version: Restores simple behavior for Homomers to prevent regression errors.

import gc
import json
import os
import shutil
import subprocess
import sys
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

def _py_exe() -> str:
    return sys.executable

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
        except Exception as e:
            print(f"  ↺ urllib retry because: {e}")
        time.sleep(sleep_sec)
    return False

def get_pdb_file(pdb_code: str, allow_upload: bool = True) -> str:
    if pdb_code:
        fn = f"{pdb_code}.pdb"
        if _download_with_retries(
            f"https://files.rcsb.org/download/{fn}", fn
        ) or _download_with_retries(f"https://files.rcsb.org/view/{fn}", fn):
            print(f"✅ Downloaded PDB to {fn}")
            return fn
        raise RuntimeError(f"Failed to download PDB for code: {pdb_code}")

    if allow_upload:
        try:
            from google.colab import files 
            print("📤 No PDB code provided. Please upload your local .pdb file:")
            uploaded = files.upload()
            if not uploaded:
                raise RuntimeError("No file uploaded.")
            name = list(uploaded.keys())[0]
            print(f"✅ Uploaded: {name}")
            return name
        except Exception as e:
            raise RuntimeError(f"Upload failed: {e}")

    raise RuntimeError("No PDB code provided and uploads are disabled.")

# ---------- ProteinMPNN setup & run ----------

def _cuda_available() -> bool:
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False

def _ensure_model_weights(root: str) -> Dict[str, bool]:
    """
    Robustly ensure model weights exist. If missing, force run the download script.
    """
    vanilla = os.path.join(root, "vanilla_model_weights")
    soluble = os.path.join(root, "soluble_model_weights")
    ca = os.path.join(root, "ca_model_weights")

    def _exists() -> Dict[str, bool]:
        def valid(p):
            if not os.path.isdir(p): return False
            return len(os.listdir(p)) > 0
        return {
            "vanilla": valid(vanilla),
            "soluble": valid(soluble),
            "ca": valid(ca),
        }

    ready = _exists()
    if all(ready.values()):
        return ready

    print("⚠️ Model weights missing or incomplete. Attempting to download...")
    
    # Fallback: Run the official download script
    helper = os.path.join(root, "get_model_weights.sh")
    if os.path.isfile(helper):
        print(f"   Running download script: {helper}")
        try:
            subprocess.run(["bash", helper], cwd=root, check=True)
            print("✅ Download script finished.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Download script failed with code {e.returncode}")
    
    return _exists()

def ensure_proteinmpnn(root: str = "/content/ProteinMPNN") -> Dict:
    if not os.path.isdir(root):
        print("📥 Cloning ProteinMPNN...")
        subprocess.run(
            ["git", "clone", "-q", "https://github.com/dauparas/ProteinMPNN.git", root],
            check=True,
        )

    print("📦 Installing Python deps (quiet)...")
    subprocess.run(
        ["pip", "install", "-q", "biopython==1.83", "einops==0.7.0"], check=True
    )

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
    _ensure_model_weights(root)
    return env

def resolve_weights(env: Dict, use_soluble_model: bool, ca_only: bool) -> str:
    if ca_only:
        w = env["weights"]["ca"]
    elif use_soluble_model:
        w = env["weights"]["soluble"]
    else:
        w = env["weights"]["vanilla"]
    if not os.path.isdir(w) or len(os.listdir(w)) == 0:
        raise RuntimeError(f"Model weights folder not found or empty: {w}")
    return w

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
    allow_upload: bool = True,
    clean_workspace: bool = False,
    auto_download: bool = False,
    pdb_path: str = "",
) -> Dict:
    """
    Main entry point.
    """
    if clean_workspace:
        clean_colab_workspace()

    # 1) PDB input
    code = (pdb_code or "").strip().upper()
    uploaded_path = (pdb_path or "").strip()
    print(
        f"[Runner] incoming: code='{code}' uploaded='{uploaded_path}' homomer={homomer}"
    )

    local_pdb = ""
    input_mode = ""

    if uploaded_path:
        if os.path.isfile(uploaded_path):
            local_pdb = uploaded_path
            input_mode = "uploaded_file"
        else:
            raise RuntimeError(f"Uploaded pdb_path not found: {uploaded_path}")
    elif code:
        local_pdb = get_pdb_file(code, allow_upload=allow_upload)
        input_mode = "pdb_code"
    else:
        if allow_upload:
            local_pdb = get_pdb_file("", allow_upload=True)
            input_mode = "colab_upload"
        else:
            raise RuntimeError("No PDB code or uploaded file provided.")

    # 2) Setup env
    env = ensure_proteinmpnn()
    root = env["root"]
    out_dir = env["out_dir"]
    weights_root = resolve_weights(env, use_soluble_model, ca_only)

    # Stage PDB
    pdb_basename = os.path.basename(local_pdb)
    staged_pdb_root = os.path.join(root, pdb_basename)
    if os.path.abspath(local_pdb) != os.path.abspath(staged_pdb_root):
        shutil.copy2(local_pdb, staged_pdb_root)
    pdb_arg_abs = os.path.abspath(staged_pdb_root)

    # 3) Build Command
    cmd = [
        _py_exe(),
        f"{root}/protein_mpnn_run.py",
        "--out_folder", out_dir,
        "--model_name", model_name,
        "--path_to_model_weights", weights_root,
        "--num_seq_per_target", str(int(num_seqs)),
        "--sampling_temp", str(float(sampling_temp)),
        "--batch_size", "1",
    ]

    if use_soluble_model:
        cmd.append("--use_soluble_model")
    if ca_only:
        cmd.append("--ca_only")

    # --- [CRITICAL FIX: RESTORE SIMPLE PATH FOR HOMOMERS] ---
    if homomer:
        # RESTORED: Simple logic for Homomer. Just pass the PDB.
        # This worked before, so it should work now.
        print("🧬 Running in simple Homomer mode (Legacy path)...")
        cmd.extend(["--pdb_path", pdb_arg_abs])
        
    else:
        # HETEROMER MODE (New logic)
        print("🧩 Running in Heteromer mode (Complex path)...")
        
        # Helpers
        helper_parse = os.path.join(root, "helper_scripts", "parse_multiple_chains.py")
        helper_assign = os.path.join(root, "helper_scripts", "assign_fixed_chains.py")
        
        jsonl_parsed = os.path.join(out_dir, "parsed_pdbs.jsonl")
        jsonl_assigned = os.path.join(out_dir, "assigned_pdbs.jsonl")