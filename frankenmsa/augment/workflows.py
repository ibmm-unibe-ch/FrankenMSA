from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import pandas as pd

from frankenmsa.augment.ghostfold import GhostFold


def normalize_ghostfold_input(input_data: str) -> str:
    """Normalize GhostFold input into a single uppercase monomer sequence."""
    if not input_data or not input_data.strip():
        raise ValueError("Please provide input data.")

    lines = [line.strip() for line in input_data.strip().splitlines() if line.strip()]
    header_lines = [line for line in lines if line.startswith(">")]
    if len(header_lines) > 1:
        raise ValueError("GhostFold augmentation accepts only one FASTA record.")

    sequence_parts = [line for line in lines if not line.startswith(">")]
    full_sequence = "".join(sequence_parts)
    full_sequence = "".join(full_sequence.split()).upper()

    if not full_sequence:
        raise ValueError("No valid sequences found.")
    if ":" in full_sequence:
        raise ValueError("GhostFold augmentation currently supports monomer sequences only.")
    if not re.fullmatch(r"[A-Z]+", full_sequence):
        raise ValueError("GhostFold input must contain only amino-acid letters.")

    return full_sequence


def build_ghostfold_result_key(
    msa_data: Optional[Dict[str, dict]], prefix: str = "ghostfold_aug"
) -> str:
    """Build the next numbered store key for GhostFold outputs."""
    msa_data = msa_data or {}
    n_existing = sum(1 for key in msa_data.keys() if key.startswith(prefix))
    return f"{prefix}_{n_existing + 1}"


def attach_ghostfold_result(
    msa_data: Optional[Dict[str, dict]],
    msa_df: pd.DataFrame,
    prefix: str = "ghostfold_aug",
) -> Tuple[Dict[str, dict], str, List[str]]:
    """Attach a GhostFold result to the app store representation."""
    msa_data = {} if not isinstance(msa_data, dict) else dict(msa_data)
    result_key = build_ghostfold_result_key(msa_data, prefix=prefix)
    msa_data[result_key] = msa_df.to_dict("list")
    return msa_data, result_key, [result_key]


def run_ghostfold_augmentation(
    input_data: str,
    msa_data: Optional[Dict[str, dict]],
    prefix: str = "ghostfold_aug",
) -> Tuple[Dict[str, dict], str, List[str], pd.DataFrame]:
    """Normalize GhostFold input, run augmentation, and attach the output."""
    sequence = normalize_ghostfold_input(input_data)
    msa_df = GhostFold().augment(sequence=sequence)
    msa_data, main_key, created_keys = attach_ghostfold_result(
        msa_data,
        msa_df,
        prefix=prefix,
    )
    return msa_data, main_key, created_keys, msa_df


__all__ = [
    "normalize_ghostfold_input",
    "build_ghostfold_result_key",
    "attach_ghostfold_result",
    "run_ghostfold_augmentation",
]