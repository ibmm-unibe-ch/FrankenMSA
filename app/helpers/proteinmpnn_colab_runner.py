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
            print(f"  ↺ retry: {e}")
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


# ---------- Splitting Logic (The Smart Way) ----------


def _split_fasta_and_generate_a3m(
    full_fasta_path, out_dir, base_name, chain_labels=None
):
    """
    Splits combined FASTA by detecting '/' separators in the sequence.
    This is how ProteinMPNN officially separates chains in output.
    """
    split_results = {}

    # 1. Read the first sequence to determine split points
    # We assume all generated sequences have the same chain structure
    with open(full_fasta_path, "r") as f:
        lines = f.readlines()

    if not lines:
        return {}

    # Find the first sequence line (skip headers)
    sample_seq = ""
    for line in lines:
        if not line.startswith(">"):
            sample_seq = line.strip()
            break

    if "/" not in sample_seq:
        print("ℹ️ No '/' separators found. Assuming single chain.")
        return {}

    # 2. Calculate lengths of each segment
    segments = sample_seq.split("/")
    lengths = [len(s) for s in segments]
    print(f"🔪 Detected {len(lengths)} chains with lengths: {lengths}")

    # 3. Process the whole file
    chain_files = {}  # Store file handles

    # Decide labels for each chain: prefer user-provided labels (e.g. PDB chain IDs)
    # when their number matches the number of detected chains; otherwise fall back
    # to alphabetical A, B, C, ...
    if chain_labels is not None and len(chain_labels) == len(lengths):
        labels = list(chain_labels)
    else:
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        labels = [alphabet[i] if i < 26 else str(i) for i in range(len(lengths))]

    try:
        # Open file handles for each chain
        for i in range(len(lengths)):
            chain_id = labels[i]
            p = os.path.join(out_dir, f"{base_name}_chain{chain_id}.fasta")
            chain_files[i] = {"path": p, "handle": open(p, "w"), "id": chain_id}

        current_header = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith(">"):
                current_header = line
            else:
                # This is a sequence line, split it by '/'
                parts = line.split("/")

                if len(parts) != len(lengths):
                    # Skip malformed lines
                    continue

                for i, seq_part in enumerate(parts):
                    # Write to respective chain file
                    # Header: >sample_1_chainA
                    cf = chain_files[i]
                    cf["handle"].write(
                        f"{current_header}_chain{cf['id']}\n{seq_part}\n"
                    )

        # Close handles and convert to A3M
        for i in chain_files:
            cf = chain_files[i]
            cf["handle"].close()

            # Convert to A3M string
            a3m = fasta_to_a3m(cf["path"])
            text = read_text_safe(Path(a3m))
            split_results[f"{base_name}_chain{cf['id']}"] = text

    except Exception as e:
        print(f"❌ Splitting failed: {e}")
        # Close any open files
        for i in chain_files:
            try:
                chain_files[i]["handle"].close()
            except:
                pass

    return split_results


# ---------- ProteinMPNN setup & run ----------


def _cuda_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _ensure_model_weights(root: str) -> Dict[str, bool]:
    vanilla = os.path.join(root, "vanilla_model_weights")
    soluble = os.path.join(root, "soluble_model_weights")
    ca = os.path.join(root, "ca_model_weights")

    def _exists() -> Dict[str, bool]:
        def valid(p):
            if not os.path.isdir(p):
                return False
            return len(os.listdir(p)) > 0

        return {
            "vanilla": valid(vanilla),
            "soluble": valid(soluble),
            "ca": valid(ca),
        }

    if all(_exists().values()):
        return _exists()

    print("⚠️ Model weights missing. Attempting download...")
    try:
        subprocess.run(
            ["git", "-C", root, "lfs", "pull"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except:
        pass

    if all(_exists().values()):
        return _exists()

    print("   [Plan C] Direct download...")
    import urllib.request

    base_url = "https://github.com/dauparas/ProteinMPNN/raw/main"
    target_file = "v_48_020.pt"
    for category in ["vanilla", "soluble", "ca"]:
        folder_name = f"{category}_model_weights"
        local_dir = os.path.join(root, folder_name)
        os.makedirs(local_dir, exist_ok=True)
        local_pt = os.path.join(local_dir, target_file)
        if not os.path.exists(local_pt) or os.path.getsize(local_pt) < 1000:
            try:
                url = f"{base_url}/{folder_name}/{target_file}?download="
                with urllib.request.urlopen(url, timeout=60) as r, open(
                    local_pt, "wb"
                ) as f:
                    shutil.copyfileobj(r, f)
            except:
                pass

    return _exists()


def ensure_proteinmpnn(root: str = "/content/ProteinMPNN") -> Dict:
    """Ensure that a usable ProteinMPNN checkout (code + weights) is available.

    This function is intentionally defensive for Colab:
    - If the folder does not exist, we clone it.
    - If the folder exists but is obviously incomplete (missing main script or helper scripts),
      we remove it and clone again. This avoids the situation where only the weights
      directory was copied/saved but the code is missing, which would later cause
      `protein_mpnn_run.py` to be not found in the subprocess call.
    """

    need_clone = False

    if not os.path.isdir(root):
        # Nothing there yet -> clone from scratch.
        need_clone = True
    else:
        # Folder exists; sanity‑check that it looks like a real ProteinMPNN repo.
        main_script = os.path.join(root, "protein_mpnn_run.py")
        helper_dir = os.path.join(root, "helper_scripts")
        if not os.path.isfile(main_script) or not os.path.isdir(helper_dir):
            print("⚠️ Existing ProteinMPNN folder seems incomplete. Re‑cloning repo...")
            try:
                shutil.rmtree(root)
            except Exception:
                # Best effort; if this fails, git clone below will raise a clearer error.
                pass
            need_clone = True

    if need_clone:
        print("📥 Cloning ProteinMPNN...")
        subprocess.run(
            ["git", "clone", "-q", "https://github.com/dauparas/ProteinMPNN.git", root],
            check=True,
        )

    print("📦 Installing Python deps...")
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
        return env["weights"]["ca"]
    elif use_soluble_model:
        return env["weights"]["soluble"]
    return env["weights"]["vanilla"]


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

    if clean_workspace:
        clean_colab_workspace()

    code = (pdb_code or "").strip().upper()
    uploaded_path = (pdb_path or "").strip()
    print(
        f"[Runner] incoming: code='{code}' uploaded='{uploaded_path}' homomer={homomer}"
    )

    local_pdb = ""
    if uploaded_path:
        if os.path.isfile(uploaded_path):
            local_pdb = uploaded_path
        else:
            raise RuntimeError(f"Uploaded pdb_path not found: {uploaded_path}")
    elif code:
        local_pdb = get_pdb_file(code, allow_upload=allow_upload)
    else:
        if allow_upload:
            local_pdb = get_pdb_file("", allow_upload=True)
        else:
            raise RuntimeError("No PDB provided.")

    env = ensure_proteinmpnn()
    root = env["root"]
    out_dir = env["out_dir"]
    weights_root = resolve_weights(env, use_soluble_model, ca_only)

    pdb_basename = os.path.basename(local_pdb)
    staged_pdb_root = os.path.join(root, pdb_basename)
    if os.path.abspath(local_pdb) != os.path.abspath(staged_pdb_root):
        shutil.copy2(local_pdb, staged_pdb_root)
    pdb_arg_abs = os.path.abspath(staged_pdb_root)

    helper_parse = os.path.join(root, "helper_scripts", "parse_multiple_chains.py")
    helper_assign = os.path.join(root, "helper_scripts", "assign_fixed_chains.py")
    jsonl_parsed = os.path.join(out_dir, "parsed_pdbs.jsonl")
    jsonl_assigned = os.path.join(out_dir, "assigned_pdbs.jsonl")
    use_jsonl_mode = False

    if not homomer:
        if os.path.exists(helper_parse) and os.path.exists(helper_assign):
            print("🧩 Configuring Heteromer mode...")
            temp_pdb_dir = os.path.join(out_dir, "temp_pdbs")
            os.makedirs(temp_pdb_dir, exist_ok=True)
            shutil.copy2(pdb_arg_abs, os.path.join(temp_pdb_dir, pdb_basename))

            try:
                subprocess.run(
                    [
                        _py_exe(),
                        helper_parse,
                        f"--input_path={temp_pdb_dir}",
                        f"--output_path={jsonl_parsed}",
                    ],
                    check=True,
                )
                d_list = split_chain_list(design_chains)
                if d_list:
                    subprocess.run(
                        [
                            _py_exe(),
                            helper_assign,
                            f"--input_path={jsonl_parsed}",
                            f"--output_path={jsonl_assigned}",
                            "--chain_list",
                            " ".join(d_list),
                        ],
                        check=True,
                    )
                    use_jsonl_mode = True
                else:
                    c_path = write_chain_jsonl(
                        out_dir, local_pdb, d_list, split_chain_list(fixed_chains)
                    )
                    if c_path:
                        jsonl_assigned = c_path
                        use_jsonl_mode = True
            except Exception as e:
                print(f"⚠️ Scripts failed: {e}. Fallback to simple mode.")
                use_jsonl_mode = False
    else:
        print("🧬 Running in simple Homomer mode...")
        use_jsonl_mode = False

    cmd = [
        _py_exe(),
        f"{root}/protein_mpnn_run.py",
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
        "--batch_size",
        "1",
    ]
    if use_soluble_model:
        cmd.append("--use_soluble_model")
    if ca_only:
        cmd.append("--ca_only")

    if use_jsonl_mode:
        cmd.extend(["--jsonl_path", jsonl_parsed])
        cmd.extend(["--chain_id_jsonl", jsonl_assigned])
    else:
        cmd.extend(["--pdb_path", pdb_arg_abs])
        if not homomer:
            c_path = write_chain_jsonl(
                out_dir,
                local_pdb,
                split_chain_list(design_chains),
                split_chain_list(fixed_chains),
            )
            if c_path:
                cmd.extend(["--chain_id_jsonl", c_path])

    print("🔧 Command:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if proc.stdout:
        print("=== STDOUT ===", proc.stdout[-1000:])
    if proc.stderr:
        print("\n=== STDERR ===", proc.stderr[-1000:])

    if proc.returncode != 0:
        stderr_tail = proc.stderr[-2000:] if proc.stderr else ""
        raise RuntimeError(
            f"ProteinMPNN run failed (code {proc.returncode})\n"
            f"STDERR tail:\n{stderr_tail}"
        )

    pdb_name = Path(local_pdb).stem
    fasta_out, n = merge_outputs_to_fasta(out_dir, pdb_name)
    print(f"✅ Merged FASTA: {fasta_out}")

    a3m_out = fasta_to_a3m(fasta_out)
    a3m_text_full = read_text_safe(Path(a3m_out))

    # --- [Smart Splitting via '/' Separator] ---
    split_chains_map = {}
    try:
        print("🔪 Attempting smart split via '/' separator...")
        split_chains_map = _split_fasta_and_generate_a3m(
            full_fasta_path=fasta_out,
            out_dir=out_dir,
            base_name=pdb_name,
            chain_labels=split_chain_list(design_chains) if design_chains else None,
        )
        print(f"✅ Split into {len(split_chains_map)} chains.")
    except Exception as e:
        print(f"⚠️ Split warning: {e}")

    zip_path = zip_outputs(out_dir, base=pdb_name, destination="/content")

    if auto_download:
        try:
            from google.colab import files

            files.download(zip_path)
        except:
            pass

    return {
        "pdb_path": local_pdb,
        "zip": zip_path,
        "homomer": homomer,
        "a3m_name": Path(a3m_out).name,
        "a3m_text": a3m_text_full,
        "split_chains": split_chains_map,
    }
