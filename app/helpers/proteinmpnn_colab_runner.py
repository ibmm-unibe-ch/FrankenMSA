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
            try:
                from IPython import get_ipython
                ip = get_ipython()
                has_kernel = bool(ip and getattr(ip, "kernel", None))
            except Exception:
                has_kernel = False
            if not has_kernel:
                raise RuntimeError(
                    "Colab upload UI is not available. Use web UI upload."
                )

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
    Robustly ensure model weights exist. 
    Tries Git LFS -> Script -> Direct Download (Plan C).
    """
    vanilla = os.path.join(root, "vanilla_model_weights")
    soluble = os.path.join(root, "soluble_model_weights")
    ca = os.path.join(root, "ca_model_weights")

    def _exists() -> Dict[str, bool]:
        # Check if directory exists AND contains .pt files
        def valid(p):
            if not os.path.isdir(p): return False
            return len([f for f in os.listdir(p) if f.endswith(".pt")]) > 0
            
        return {
            "vanilla": valid(vanilla),
            "soluble": valid(soluble),
            "ca": valid(ca),
        }

    # If everything is already there, return immediately
    ready = _exists()
    if all(ready.values()):
        return ready

    print("⚠️ Model weights missing or incomplete. Starting download sequence...")

    # 1. Try git lfs pull first
    try:
        print("   [Plan A] Attempting 'git lfs pull'...")
        subprocess.run(
            ["git", "-C", root, "lfs", "pull"], 
            check=False, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

    if all(_exists().values()):
        print("✅ Weights retrieved via Git LFS.")
        return _exists()

    # 2. Fallback: Run the official download script
    helper = os.path.join(root, "get_model_weights.sh")
    if os.path.isfile(helper):
        print(f"   [Plan B] Running download script: {helper}")
        try:
            subprocess.run(
                ["bash", helper], 
                cwd=root, 
                check=True,
                stdout=None, 
                stderr=None
            )
        except subprocess.CalledProcessError:
            print(f"   ❌ Download script failed.")
    
    if all(_exists().values()):
        print("✅ Weights retrieved via script.")
        return _exists()

    # 3. Last Resort: Direct Python Download (Plan C)
    # Mimics 'wget' but in python, for the specific v_48_020.pt file
    print("   [Plan C] Attempting direct download from GitHub...")
    import urllib.request
    
    base_url = "https://github.com/dauparas/ProteinMPNN/raw/main"
    # We only ensure the standard model used by default
    target_file = "v_48_020.pt"
    
    for category in ["vanilla", "soluble", "ca"]:
        folder_name = f"{category}_model_weights"
        local_dir = os.path.join(root, folder_name)
        os.makedirs(local_dir, exist_ok=True)
        
        local_pt = os.path.join(local_dir, target_file)
        if not os.path.exists(local_pt) or os.path.getsize(local_pt) < 1000:
            remote_url = f"{base_url}/{folder_name}/{target_file}?download="
            print(f"    Downloading {category}/{target_file} ...")
            try:
                with urllib.request.urlopen(remote_url, timeout=60) as r, open(local_pt, "wb") as f:
                    shutil.copyfileobj(r, f)
                print(f"    ✅ Downloaded {category}.")
            except Exception as e:
                print(f"    ❌ Direct download failed for {category}: {e}")

    return _exists()

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

    # Check and fetch weights if needed
    weights_ready = _ensure_model_weights(root)

    return env

def resolve_weights(env: Dict, use_soluble_model: bool, ca_only: bool) -> str:
    if ca_only:
        w = env["weights"]["ca"]
    elif use_soluble_model:
        w = env["weights"]["soluble"]
    else:
        w = env["weights"]["vanilla"]
    
    if not os.path.isdir(w) or len(os.listdir(w)) == 0:
        # Check specifically for the file we likely need
        if not os.path.exists(os.path.join(w, "v_48_020.pt")):
             # Trigger check again just in case
             _ensure_model_weights(env["root"])
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
    Main entry point: does the whole workflow and returns a summary dict.
    Supports both Homomer (Example 6) and Heteromer (Example 2) workflows.
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
    import shutil
    pdb_basename = os.path.basename(local_pdb)
    staged_pdb_root = os.path.join(root, pdb_basename)
    
    if os.path.abspath(local_pdb) != os.path.abspath(staged_pdb_root):
        shutil.copy2(local_pdb, staged_pdb_root)
    
    pdb_arg_abs = os.path.abspath(staged_pdb_root)

    # 3) Prepare Chain Controls
    helper_parse = os.path.join(root, "helper_scripts", "parse_multiple_chains.py")
    helper_tie = os.path.join(root, "helper_scripts", "make_tied_positions_dict.py")
    helper_assign = os.path.join(root, "helper_scripts", "assign_fixed_chains.py")
    
    designed_list = split_chain_list(design_chains)
    fixed_list = split_chain_list(fixed_chains)
    
    jsonl_parsed = os.path.join(out_dir, "parsed_pdbs.jsonl")
    jsonl_tied = os.path.join(out_dir, "tied_pdbs.jsonl")
    jsonl_assigned = os.path.join(out_dir, "assigned_pdbs.jsonl")
    
    use_jsonl_mode = False
    
    if os.path.exists(helper_parse):
        print("🧬 Parsing PDB chains...")
        temp_pdb_dir = os.path.join(out_dir, "temp_pdbs")
        os.makedirs(temp_pdb_dir, exist_ok=True)
        shutil.copy2(pdb_arg_abs, os.path.join(temp_pdb_dir, pdb_basename))
        
        subprocess.run(
            [_py_exe(), helper_parse, f"--input_path={temp_pdb_dir}", f"--output_path={jsonl_parsed}"],
            check=True
        )
        
        if homomer and os.path.exists(helper_tie):
            print("🔗 Generating tied positions for Homomer...")
            subprocess.run(
                [_py_exe(), helper_tie, f"--input_path={jsonl_parsed}", f"--output_path={jsonl_tied}", "--homooligomer", "1"], 
                check=True
            )
            use_jsonl_mode = True
            
        elif not homomer and os.path.exists(helper_assign):
            print("🧩 Configuring chains for Heteromer/Fixed design...")
            chains_to_design_str = ""
            if designed_list:
                chains_to_design_str = " ".join(designed_list)
            
            if chains_to_design_str:
                subprocess.run(
                    [_py_exe(), helper_assign, f"--input_path={jsonl_parsed}", f"--output_path={jsonl_assigned}", "--chain_list", chains_to_design_str],
                    check=True
                )
                use_jsonl_mode = True
            else:
                chain_jsonl_path = write_chain_jsonl(out_dir, local_pdb, designed_list, fixed_list)
                if chain_jsonl_path:
                    jsonl_assigned = chain_jsonl_path
                    use_jsonl_mode = True

    # 4) Build Command
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

    if use_jsonl_mode:
        cmd.extend(["--jsonl_path", jsonl_parsed])
        if homomer:
            cmd.extend(["--tied_positions_jsonl", jsonl_tied])
        else:
            cmd.extend(["--chain_id_jsonl", jsonl_assigned])
    else:
        cmd.extend(["--pdb_path", pdb_arg_abs])
        if not homomer:
             chain_jsonl_path = write_chain_jsonl(out_dir, local_pdb, designed_list, fixed_list)
             if chain_jsonl_path:
                 cmd.extend(["--chain_id_jsonl", chain_jsonl_path])

    # 5) Execute
    print("🔧 Command:\n ", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    
    if proc.stdout:
        print("=== STDOUT ===")
        print(proc.stdout[-2000:])
    if proc.stderr:
        print("\n=== STDERR ===")
        print(proc.stderr[-2000:])

    if proc.returncode != 0:
        raise RuntimeError("ProteinMPNN run failed. See logs above.")

    # 6) Merge outputs -> FASTA
    pdb_name = Path(local_pdb).stem
    fasta_out, n = merge_outputs_to_fasta(out_dir, pdb_name)
    print(f"✅ Merged FASTA: {fasta_out} (N={n} sequences)")

    # 7) Minimal A3M
    a3m_out = fasta_to_a3m(fasta_out)
    print(f"✅ Minimal A3M: {a3m_out}")

    a3m_path_obj = Path(a3m_out)
    a3m_name = a3m_path_obj.name
    a3m_text = read_text_safe(a3m_path_obj)

    # 8) Zip outputs
    zip_path = zip_outputs(out_dir, base=pdb_name, destination="/content")
    print(f"🗜️  Zipped outputs: {zip_path}")

    if auto_download:
        try:
            from google.colab import files as colab_files
            colab_files.download(zip_path)
        except Exception:
            pass

    return {
        "pdb_path": local_pdb,
        "out_dir": out_dir,
        "fasta": fasta_out,
        "a3m": a3m_out,
        "zip": zip_path,
        "num_sequences": n,
        "cuda_available": env["cuda_available"],
        "homomer": homomer,
        "a3m_name": a3m_name,
        "a3m_text": a3m_text,
    }