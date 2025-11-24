"""Shared helpers for ProteinMPNN runners.

These utilities wrap the small pieces that both the Colab and
local runners rely on (chain parsing, FASTA/A3M conversion, etc.).
"""

from __future__ import annotations

import glob
import json
import os
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

__all__ = [
    "split_chain_list",
    "write_chain_jsonl",
    "merge_outputs_to_fasta",
    "fasta_to_a3m",
    "zip_outputs",
    "read_text_safe",
]


def split_chain_list(csv_value: str) -> List[str]:
    """Return a normalized list of single-letter chain identifiers."""
    csv_value = (csv_value or "").strip()
    if not csv_value:
        return []
    parts = [p.strip().upper() for p in csv_value.replace(";", ",").split(",")]
    return [p for p in parts if p and len(p) == 1 and p.isalpha()]


def write_chain_jsonl(
    out_dir: str,
    pdb_path: str,
    designed: List[str],
    fixed: List[str],
) -> Optional[str]:
    """Generate a ProteinMPNN chain selection JSONL when needed."""
    if not (designed or fixed):
        return None

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "name": Path(pdb_path).stem,
        "design_chain_list": designed,
        "fixed_chain_list": fixed,
    }
    jsonl_path = Path(out_dir) / "chain_id.jsonl"
    jsonl_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return str(jsonl_path)


def merge_outputs_to_fasta(out_dir: str, stem: str) -> Tuple[str, int]:
    """Merge scattered ProteinMPNN FASTA fragments into one FASTA file."""
    fasta_path = Path(out_dir) / f"{stem}_proteinmpnn.fasta"
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


def fasta_to_a3m(fasta_path: str) -> str:
    """Convert an in-memory FASTA to the minimal A3M format."""
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


def zip_outputs(out_dir: str, base: str, destination: Optional[str] = None) -> str:
    """Zip ProteinMPNN outputs and return the archive path."""
    dest_dir = Path(destination).expanduser() if destination else Path(out_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / f"{base}_proteinmpnn_outputs.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in glob.glob(os.path.join(out_dir, "**", "*"), recursive=True):
            if os.path.isfile(filename):
                archive.write(filename, arcname=os.path.relpath(filename, out_dir))
    return str(zip_path)


def read_text_safe(path: str) -> str:
    """Load text while ignoring encoding glitches."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return Path(path).read_text(errors="ignore")
