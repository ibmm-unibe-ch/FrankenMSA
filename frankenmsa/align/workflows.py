import re
from typing import Dict, List, Optional, Tuple

import pandas as pd

from frankenmsa.utils.fileio import read_fasta


def normalize_mmseqs_input(input_data: str) -> str:
    """Normalize raw MMseqs input text into a single uppercase sequence string."""
    if not input_data or not input_data.strip():
        raise ValueError("Please provide input data.")

    sequence_parts = []
    for line in input_data.strip().splitlines():
        line = line.strip()
        if not line or line.startswith(">"):  # tolerate FASTA-like headers
            continue
        sequence_parts.append(line)

    full_sequence = "".join(sequence_parts)
    full_sequence = "".join(full_sequence.split()).upper()

    if not full_sequence:
        raise ValueError("No valid sequences found.")

    return full_sequence


def validate_mmseqs_request(sequence: str, pairing_mode: str) -> bool:
    """Validate the MMseqs request and return whether it is multimeric."""
    if pairing_mode not in {"none", "greedy", "complete"}:
        raise ValueError("Invalid pairing mode.")

    is_multimer = ":" in sequence
    if is_multimer and pairing_mode == "none":
        raise ValueError(
            "You have ':' in sequence but selected 'None'. Please select 'Greedy' or 'All'."
        )
    if not is_multimer and pairing_mode != "none":
        raise ValueError(
            "Single sequence provided but 'Greedy/All' selected. Please select 'None'."
        )
    return is_multimer


def build_result_key(msa_data: Optional[Dict[str, dict]], base_name: str) -> str:
    """Build the next numbered result key for an MSA prefix."""
    msa_data = msa_data or {}
    n_existing = sum(
        1 for key in msa_data.keys() if key.startswith(base_name) and "chain" not in key
    )
    return f"{base_name}_{n_existing + 1}"


def attach_alignment_result(
    msa_data: Optional[Dict[str, dict]],
    key: str,
    msa_df: pd.DataFrame,
    multimer_header_str: Optional[str] = None,
) -> Dict[str, dict]:
    """Store an alignment DataFrame in the app store representation."""
    msa_data = {} if not isinstance(msa_data, dict) else dict(msa_data)
    data_dict = msa_df.to_dict("list")
    if multimer_header_str:
        data_dict["_multimer_header"] = [multimer_header_str] * len(msa_df)
    msa_data[key] = data_dict
    return msa_data


def parse_plm_input(input_data: str) -> Tuple[List[str], List[str]]:
    """Parse PLM-Search input using the shared FASTA reader."""
    if not input_data or not input_data.strip():
        raise ValueError("Please provide input data.")

    sequences, descriptions = read_fasta(input_data)
    if not sequences:
        raise ValueError("No valid sequences found.")
    return sequences, descriptions


def validate_similarity_cutoff(similarity_cutoff: float) -> None:
    """Validate the PLM-Search similarity cutoff."""
    if similarity_cutoff is None or not (0.0 <= similarity_cutoff <= 1.0):
        raise ValueError("Similarity cutoff must be between 0.0 and 1.0.")


def sanitize_result_token(value: str) -> str:
    """Sanitize a value for use in generated MSA keys."""
    token = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("_")
    return token or "query"


def attach_plm_search_results(
    msa_data: Optional[Dict[str, dict]],
    df: pd.DataFrame,
    prefix: str = "plm_search",
) -> Tuple[Dict[str, dict], Optional[str], List[str]]:
    """Split PLM-Search results by query and attach them to the MSA store."""
    if df is None or df.empty:
        return ({} if msa_data is None else msa_data), None, []

    msa_data = {} if not isinstance(msa_data, dict) else dict(msa_data)
    unique_queries = df["query"].unique()
    n_existing = sum(1 for key in msa_data.keys() if key.startswith(prefix))
    new_keys: List[str] = []

    for idx, query in enumerate(unique_queries):
        query_df = df[df["query"] == query][["header", "sequence"]].copy()
        safe_query = sanitize_result_token(query)
        new_key = f"{prefix}_{safe_query}_{n_existing + idx + 1}"
        msa_data[new_key] = query_df.to_dict("list")
        new_keys.append(new_key)

    main_key = new_keys[0] if new_keys else None
    return msa_data, main_key, new_keys


__all__ = [
    "normalize_mmseqs_input",
    "validate_mmseqs_request",
    "build_result_key",
    "attach_alignment_result",
    "parse_plm_input",
    "validate_similarity_cutoff",
    "sanitize_result_token",
    "attach_plm_search_results",
]