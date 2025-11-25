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

# Import BioPython
try:
    from Bio import PDB
except ImportError:
    pass

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
        os.system("rm -f /content/*.zip /content/*.fa /content/*.fasta /content/*.a3m 2>/dev/null")
    except Exception:
        pass
    gc.collect()
    print("done.")

def _download_with_retries(url: str, out_path: str, tries: int = 4, sleep_sec: float = 1.5) -> bool:
    import urllib.request, urllib.error, time
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    for i in range(1, tries + 1):
        try:
            print(f"🌐 [urllib] {url} (try {i}/{tries})...")
            with urllib.request.urlopen(req, timeout=20) as r, open(out_path, "wb") as f:
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

# ---------- Helper: Native PDB Parser (Replaces parse_multiple_chains.py) ----------

def _parse_pdb_to_jsonl(pdb_path, out_jsonl_path):
    """
    Native implementation of parse_multiple_chains.py using BioPython.
    Parses PDB and writes the 'parsed_pdbs.jsonl' format expected by ProteinMPNN.
    """
    print(f"🧬 Native parsing of {pdb_path} -> {out_jsonl_path}")
    
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("input", pdb_path)
    
    # Dictionary to hold parsed data
    parsed_dict = {"name": Path(pdb_path).stem}
    
    for model in structure:
        for chain in model:
            # Get sequence of CA atoms
            seq_str = ""
            coords = []
            for residue in chain:
                if PDB.is_aa(residue, standard=False) and 'CA' in residue:
                    # Convert 3-letter to 1-letter
                    resname = residue.get_resname()
                    # Handle non-standard? For now assume standard or map simply
                    try:
                        one_letter = PDB.Polypeptide.three_to_one(resname)
                    except:
                        one_letter = 'X'
                    
                    seq_str += one_letter
                    
                    # Get CA coords
                    ca = residue['CA']
                    coords.append(ca.get_coord().tolist())
            
            if seq_str:
                # Add to dict keys expected by ProteinMPNN
                parsed_dict[f"seq_chain_{chain.id}"] = seq_str
                # ProteinMPNN expects coords as list of lists of coords [N, CA, C, O]
                # But parse_multiple_chains.py output is complex.
                # ACTUALLY: ProteinMPNN's run script accepts --pdb_path directly too!
                # But for chain_id_jsonl to work, it needs matching keys.
                # Let's simplify: We don't actually need to generate parsed_pdbs.jsonl!
                # ProteinMPNN_run.py can take --pdb_path AND --chain_id_jsonl together.
                pass
        break
    
    # NOTE: After re-reading ProteinMPNN source, it turns out we DON'T need parsed_pdbs.jsonl
    # if we provide --pdb_path. The script will parse the PDB internally.
    # The only requirement is that chain_id_jsonl keys match the PDB name.
    
    return True

# ---------- Splitting Logic ----------

def _get_chain_lengths(pdb_path):
    try:
        parser = PDB.PDBParser(QUIET=True)
        structure = parser.get_structure("input", pdb_path)
    except Exception:
        return []

    chain_info = []
    MIN_RESIDUE_COUNT = 10 

    for model in structure:
        for chain in model:
            valid_residues = []
            for r in chain:
                if PDB.is_aa(r, standard=False) and 'CA' in r:
                    valid_residues.append(r)
            
            if len(valid_residues) > MIN_RESIDUE_COUNT:
                print(f"      ✅ Keeping chain {chain.id} (Length {len(valid_residues)})")
                chain_info.append((chain.id, len(valid_residues)))
            else:
                if len(valid_residues) > 0:
                     print(f"      🗑️ Dropping chain {chain.id} (Length {len(valid_residues)})")
        break 
    return chain_info

def _split_fasta_and_generate_a3m(full_fasta_path, chain_info, out_dir, base_name):
    split_results = {}
    headers = []
    seqs = []
    
    with open(full_fasta_path, 'r') as f:
        current_h = None
        current_s = []
        for line in f:
            line = line.strip()
            if not line: continue
            if line.startswith(">"):
                if current_h:
                    headers.append(current_h)
                    seqs.append("".join(current_s))
                current_h = line
                current_s = []
            else:
                current_s.append(line)
        if current_h:
            headers.append(current_h)
            seqs.append("".join(current_s))

    if not seqs: return {}
    
    cumulative_start = 0
    for chain_id, length in chain_info:
        if cumulative_start >= len(seqs[0]):
            break

        chain_fasta_path = os.path.join(out_dir, f"{base_name}_chain{chain_id}.fasta")
        
        with open(chain_fasta_path, 'w') as f_out:
            for h, s in zip(headers, seqs):
                segment = s[cumulative_start : cumulative_start + length]
                f_out.write(f"{h}_chain{chain_id}\n{segment}\n")
        
        chain_a3m = fasta_to_a3m(chain_fasta_path)
        a3m_text = read_text_safe(Path(chain_a3m))
        split_results[f"{base_name}_chain{chain_id}"] = a3m_text
        
        cumulative_start += length

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
            if not os.path.isdir(p): return False
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
        subprocess.run(["git", "-C", root, "lfs", "pull"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except: pass
    
    if all(_exists().values()): return _exists()

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
                with urllib.request.urlopen(url, timeout=60) as r, open(local_pt, "wb") as f:
                    shutil.copyfileobj(r, f)
            except: pass
            
    return _exists()

def ensure_proteinmpnn(root: str = "/content/ProteinMPNN") -> Dict:
    if not os.path.isdir(root):
        print("📥 Cloning ProteinMPNN...")
        subprocess.run(["git", "clone", "-q", "https://github.com/dauparas/ProteinMPNN.git", root], check=True)

    print("📦 Installing Python deps...")
    subprocess.run(["pip", "install", "-q", "biopython==1.83", "einops==0.7.0"], check=True)

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
    if ca_only: return env["weights"]["ca"]
    elif use_soluble_model: return env["weights"]["soluble"]
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
    print(f"[Runner] incoming: code='{code}' uploaded='{uploaded_path}' homomer={homomer}")

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

    # 4) Build Command
    # We simplified this: NO MORE helper scripts for parsing.
    # We rely on ProteinMPNN's ability to take --pdb_path + --chain_id_jsonl directly.
    
    cmd = [
        _py_exe(), f"{root}/protein_mpnn_run.py",
        "--out_folder", out_dir,
        "--model_name", model_name,
        "--path_to_model_weights", weights_root,
        "--num_seq_per_target", str(int(num_seqs)),
        "--sampling_temp", str(float(sampling_temp)),
        "--batch_size", "1",
        "--pdb_path", pdb_arg_abs # Always pass PDB path!
    ]
    if use_soluble_model: cmd.append("--use_soluble_model")
    if ca_only: cmd.append("--ca_only")

    if not homomer:
        # Heteromer Mode: Just add the chain_id_jsonl
        print("🧩 Heteromer Mode: Configuring chain constraints...")
        d_list = split_chain_list(design_chains)
        f_list = split_chain_list(fixed_chains)
        
        c_path = write_chain_jsonl(out_dir, local_pdb, d_list, f_list)
        if c_path:
            cmd.extend(["--chain_id_jsonl", c_path])
    else:
        print("🧬 Homomer Mode: Running standard.")

    # 5) Execute
    print("🔧 Command:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if proc.stdout: print("=== STDOUT ===", proc.stdout[-1000:])
    if proc.stderr: print("\n=== STDERR ===", proc.stderr[-1000:])

    if proc.returncode != 0:
        raise RuntimeError(f"ProteinMPNN run failed (code {proc.returncode}). See logs above.")

    # 6) Merge
    pdb_name = Path(local_pdb).stem
    fasta_out, n = merge_outputs_to_fasta(out_dir, pdb_name)
    print(f"✅ Merged FASTA: {fasta_out}")

    a3m_out = fasta_to_a3m(fasta_out)
    a3m_text_full = read_text_safe(Path(a3m_out))
    
    # Split
    split_chains_map = {}
    try:
        chain_info = _get_chain_lengths(local_pdb)
        if len(chain_info) > 1:
            print("🔪 Splitting chains...")
            split_chains_map = _split_fasta_and_generate_a3m(fasta_out, chain_info, out_dir, pdb_name)
    except Exception as e:
        print(f"⚠️ Splitting skipped: {e}")

    # Zip
    zip_path = zip_outputs(out_dir, base=pdb_name, destination="/content")
    
    if auto_download:
        try:
            from google.colab import files
            files.download(zip_path)
        except: pass

    return {
        "pdb_path": local_pdb,
        "zip": zip_path,
        "homomer": homomer,
        "a3m_name": Path(a3m_out).name,
        "a3m_text": a3m_text_full,
        "split_chains": split_chains_map
    }