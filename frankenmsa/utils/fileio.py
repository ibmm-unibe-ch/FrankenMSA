"""
Functions to read and write files.
"""

import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Generator


def chain_label(index: int) -> str:
    """Return spreadsheet-style chain labels: A-Z, AA-AZ, BA-BZ, ..."""
    if index < 0:
        raise ValueError("Chain index must be non-negative")
    if index < 26:
        return chr(65 + index)
    first = chr(65 + (index // 26) - 1)
    second = chr(65 + (index % 26))
    return first + second


def is_multimer_a3m_text(text: str) -> bool:
    """Return whether the text starts with a ColabFold-style multimer header."""
    lines = text.strip().splitlines()
    if not lines:
        return False
    return bool(re.match(r"^#\d+[,\d]*\t\d+[,\d]*$", lines[0].strip()))


def _parse_a3m_simple(path: str) -> List[Tuple[str, str]]:
    """Read A3M records while skipping the optional multimer header line."""
    records = []
    header = None
    seq_buf = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line:
                continue
            if line.startswith("#"):
                continue
            if line.startswith(">"):
                if header is not None:
                    records.append((header, "".join(seq_buf)))
                header = line[1:].strip()
                seq_buf = []
            else:
                seq_buf.append(line)
    if header is not None:
        records.append((header, "".join(seq_buf)))
    return records


def split_multimer_a3m_file(path: str, base_name: str) -> Dict[str, pd.DataFrame]:
    """
    Split a ColabFold-style multimer A3M into one DataFrame per chain.

    See Also
    --------
    :func:`chain_label` : Generates chain labels for output.
    :func:`_parse_a3m_simple` : Parses A3M records.
    """
    records = _parse_a3m_simple(path)

    if not records:
        raise ValueError("Empty A3M file")

    with open(path, "r", encoding="utf-8") as fh:
        first_line = fh.readline().strip()

    if not first_line.startswith("#"):
        raise ValueError("Not a valid multimer A3M")

    header_parts = first_line[1:].split("\t")
    if not header_parts or not header_parts[0]:
        raise ValueError("Invalid multimer header format")

    lengths = [int(value) for value in header_parts[0].split(",")]
    num_chains = len(lengths)

    filtered_records = []
    for header, seq in records:
        if re.match(r"^\d+$", header.strip()):
            continue
        filtered_records.append((header, seq))

    chain_msas = {}
    cumulative_lengths = [0]
    for length in lengths:
        cumulative_lengths.append(cumulative_lengths[-1] + length)

    for chain_idx in range(num_chains):
        start = cumulative_lengths[chain_idx]
        end = cumulative_lengths[chain_idx + 1]
        label = chain_label(chain_idx)

        chain_records = []
        for header, seq in filtered_records:
            chain_seq = seq[start:end].replace("-", "")
            if chain_seq:
                chain_records.append({"header": header, "sequence": chain_seq})

        if chain_records:
            chain_msas[f"{base_name}{label}"] = pd.DataFrame(chain_records)

    return chain_msas


def parse_a3m(path: str) -> List[Tuple[str, str]]:
    records = []
    header = None
    seq_chunks = []
    with open(path, "r") as fh:
        for line in fh:
            line = line.rstrip("\n").strip().replace("\00","")
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    records.append((header, "".join(seq_chunks)))
                header = line.strip()
                seq_chunks = []
            else:
                seq_chunks.append(line)
        if header is not None:
            records.append((header, "".join(seq_chunks)))
    if not records:
        raise ValueError(f"Empty or invalid A3M: {path}")
    return records


def combine_unpaired_a3m(
    input_paths: List[str],
    output_path: str,
    add_anchor: bool = True,
) -> None:
    import tempfile

    if not output_path or output_path.strip() in ("/", ".", "./"):
        out = Path(tempfile.gettempdir()) / "frankenmsa_multimer.a3m"
    else:
        out = Path(output_path)

        if out.is_dir() or str(out).endswith(("/", "\\")):
            out = out / "multimer.a3m"

        if not out.parent.exists() or str(out.parent) == "":
            out = Path(tempfile.gettempdir()) / out.name

    out.parent.mkdir(parents=True, exist_ok=True)

    chains = [parse_a3m(path) for path in input_paths]

    if not all(len(chain) > 0 for chain in chains):
        raise ValueError("One or more A3M files are empty or invalid.")

    min_rows = min(len(chain) for chain in chains)
    if any(len(chain) != min_rows for chain in chains):
        print(f"[WARN] Truncating chains to {min_rows} records to equalize row count.")
        chains = [chain[:min_rows] for chain in chains]

    def _pad(seq: str, target: int) -> str:
        return seq + ("-" * (target - len(seq))) if len(seq) < target else seq

    norm_chains = []
    per_chain_lengths = []
    for chain in chains:
        max_len = max(len(seq) for _, seq in chain)
        per_chain_lengths.append(max_len)
        norm_chains.append([(header, _pad(seq, max_len)) for header, seq in chain])

    chains = norm_chains
    lengths = per_chain_lengths
    card = ["1"] * len(chains)
    header_line = (
        f"#" + ",".join(str(length) for length in lengths) + "\t" + ",".join(card)
    )

    lines = [header_line]

    if add_anchor:
        lines.append(">"+"\t".join([str(101+it) for it in range(len(chains))]))
        anchor_seq = "".join(chains[i][0][1] for i in range(len(chains)))
        lines.append(anchor_seq)

    for chain_idx, chain in enumerate(chains):
        pad_left = sum(lengths[:chain_idx])
        pad_right = sum(lengths[chain_idx + 1 :])
        for header, seq in chain:
            seq = seq.replace(" ", "")
            header_clean = header.replace("\t", " ").strip()
            lines.append(header_clean)
            lines.append("-" * pad_left + seq + "-" * pad_right)

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_a3m_with_chains(filename: str) -> pd.DataFrame:
    """
    Read an A3M file and automatically detect if it's multimeric.
    If multimeric, returns a DataFrame with a "chain" column separating chains.
    If monomeric, returns None.

    See Also
    --------
    :func:`read_a3m` : Fallback for monomeric A3M files.
    """

    with open(filename, "r") as f:
        lines = [line.rstrip("\n") for line in f]

    first_real_line = None
    first_real_idx = 0
    for i, line in enumerate(lines):
        if line.strip():
            first_real_line = line
            first_real_idx = i
            break

    if first_real_line is None:
        raise ValueError(f"Empty A3M file: {filename}")

    if first_real_line.startswith("#"):
        header_parts = first_real_line.split("\t")
        chain_lengths_str = header_parts[0].lstrip("#")
        chain_lengths = [int(x) for x in chain_lengths_str.split(",")]

        cumsum = [0]
        for length in chain_lengths:
            cumsum.append(cumsum[-1] + length)

        headers = []
        sequences = []
        chains = []

        for i in range(first_real_idx + 1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            if line.startswith(">"):
                headers.append(line[1:])
            else:
                gap_count = 0
                for char in line:
                    if char == "-":
                        gap_count += 1
                    else:
                        break

                chain_idx = None
                for j in range(len(chain_lengths)):
                    if cumsum[j] <= gap_count < cumsum[j + 1]:
                        chain_idx = j
                        break

                if chain_idx is None:
                    chain_idx = len(chain_lengths) - 1

                seq_start = cumsum[chain_idx]
                seq_end = cumsum[chain_idx + 1]
                actual_seq = line[seq_start:seq_end]

                sequences.append(actual_seq)
                chains.append(chain_idx)

        return pd.DataFrame(
            {
                "header": headers,
                "sequence": sequences,
                "chain": chains,
                "_multimer_header": [first_real_line] * len(headers),
            }
        )

    return None


def read_a3m(filename: str) -> pd.DataFrame:
    """
    Read an A3M file and return a DataFrame with the sequences and their headers.
    Automatically detects if the file contains a multimeric assembly (if first line is # comment)
    and adds a "chain" column if multimeric.

    Parameters
    ----------
    filename : str
        The path to the A3M file.

    Returns
    -------
    pd.DataFrame
        A DataFrame with "header" and "sequence" columns. If multimeric, also includes
        a "chain" column (0-indexed) indicating which chain each sequence belongs to,
        and a "_multimer_header" column to preserve the multimer metadata for writing.

    See Also
    --------
    :func:`read_a3m_with_chains` : Handles multimeric A3M files.
    """

    # Try to read as multimeric first
    result = read_a3m_with_chains(filename)
    if result is not None:
        return result

    # Fall back to monomeric format
    headers = []
    sequences = []

    current_header = None
    current_seq_parts = []

    # Open the A3M file and read it line by line
    with open(filename, "r") as f:
        for line in f:
            line = line.strip().replace("\00","")
            if not line:
                continue

            if line.startswith("#"):
                # comment/multimer header; skip
                continue

            if line.startswith(">"):
                if current_header is not None:
                    headers.append(current_header)
                    sequences.append("".join(current_seq_parts))

                current_header = line[1:]
                current_seq_parts = []
            else:
                # Sequence lines may be split across multiple lines
                current_seq_parts.append(line)

    if current_header is not None:
        headers.append(current_header)
        sequences.append("".join(current_seq_parts))

    out = pd.DataFrame({"header": headers, "sequence": sequences})
    return out


def iter_a3m(filename: str) -> Generator[Tuple[str, str], None, None]:
    """
    Iterate over an A3M file and yield the header and sequence for each entry.

    Parameters
    ----------
    filename : str
        The path to the A3M file.

    Yields
    ------
    tuple
        A tuple containing the header and sequence for each entry.
    """

    # Open the A3M file and read it line by line
    with open(filename, "r") as f:
        header = None
        sequence = ""
        for line in f:
            # Strip whitespace from the line, remove null characters, and skip empty lines
            line = line.strip().replace("\00","")
            if not line:
                continue

            if line.startswith("#"):
                continue

            # If the line starts with '>', it's a header
            if line.startswith(">"):
                if header is not None:
                    yield (header, sequence)
                header = line[1:]
                sequence = ""
            else:
                sequence += line

        if header is not None:
            yield (header, sequence)


def write_a3m(df: pd.DataFrame, filename: str) -> None:
    """
    Write a DataFrame to an A3M file.
    Modified to support ColabFold Multimer headers.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to write to the A3M file.
    filename : str
        The path to the A3M file.
    """

    # 1. Detect Multimer Header
    # In align.py, we stored the header string in a column named "_multimer_header"
    multimer_header_line = None

    # Check if input is a dict (from Dash Store) or DataFrame
    if isinstance(df, dict):
        df = pd.DataFrame(df)

    if "_multimer_header" in df.columns and not df.empty:
        # The header string is repeated in every row, so we just take the first one
        # It usually looks like: #100,100<tab>1,1
        val = df.iloc[0]["_multimer_header"]
        if val and isinstance(val, str) and val.startswith("#"):
            multimer_header_line = val

    # 2. Define row formatter
    if "header" in df.columns:
        format_entry = lambda index, row: f">{row['header']}\n{row['sequence']}\n"
    else:
        format_entry = lambda index, row: f">seq{index}\n{row['sequence']}\n"

    # 3. Write File
    with open(filename, "w") as f:

        # [CRITICAL STEP] Write the Multimer Header first if it exists
        if multimer_header_line:
            f.write(f"{multimer_header_line}\n")

        # Write sequences
        for index, row in df.iterrows():
            f.write(format_entry(index, row))


def encode_a3m(df: pd.DataFrame) -> str:
    """
    Encode a DataFrame to an A3M string.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to encode to the A3M string.

    Returns
    -------
    str
        The A3M string.
    """
    # Optional: Add multimer support here too if needed for string display
    res = ""
    if "_multimer_header" in df.columns and not df.empty:
        val = df.iloc[0]["_multimer_header"]
        if val and str(val).startswith("#"):
            res += f"{val}\n"

    res += "".join(
        [f">{row['header']}\n{row['sequence']}\n" for _, row in df.iterrows()]
    )
    return res


def decode_a3m(a3m_str: str) -> pd.DataFrame:
    """
    Decode an A3M string to a DataFrame.

    Parameters
    ----------
    a3m_str : str
        The A3M string to decode to the DataFrame.

    Returns
    -------
    pd.DataFrame
        The DataFrame.
    """

    lines = a3m_str.strip().split("\n")
    headers = []
    sequences = []
    current_header = None
    current_seq_parts: list[str] = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(">"):
            if current_header is not None:
                headers.append(current_header)
                sequences.append("".join(current_seq_parts))
            current_header = line[1:]
            current_seq_parts = []
        else:
            current_seq_parts.append(line)

    if current_header is not None:
        headers.append(current_header)
        sequences.append("".join(current_seq_parts))

    return pd.DataFrame({"header": headers, "sequence": sequences})


def read_fasta(input_text: str) -> tuple[list[str], list[str]]:
    """
    Parse FASTA format text and return sequences and descriptions.

    Parameters
    ----------
    input_text : str
        Input text in FASTA format or plain sequence format.

    Returns
    -------
    tuple[list[str], list[str]]
        Tuple of (sequences, descriptions).
    """
    sequences = []
    descriptions = []
    current_desc = None
    current_seq = []

    for line in input_text.strip().split("\n"):
        line = line.strip().replace("\00","")
        if not line:
            continue
        if line.startswith(">"):
            if current_desc and current_seq:
                sequences.append("".join(current_seq))
                descriptions.append(current_desc)
            current_desc = line[1:]
            current_seq = []
        else:
            current_seq.append(line)

    # Add last sequence if exists
    if current_desc and current_seq:
        sequences.append("".join(current_seq))
        descriptions.append(current_desc)

    return sequences, descriptions


def split_dataframe_by_chain(
    df: pd.DataFrame, base_name: str
) -> Dict[str, pd.DataFrame]:
    """Split a DataFrame with a `chain` column into one DataFrame per chain."""

    if "chain" not in df.columns:
        raise ValueError("DataFrame does not have a 'chain' column")

    chain_msas = {}
    unique_chains: List[str] = sorted(df["chain"].dropna().unique())

    for chain_value in unique_chains:
        chain_df = df[df["chain"] == chain_value].copy()
        chain_df = chain_df.drop(columns=["chain"])
        label = (
            chain_value
            if isinstance(chain_value, str) and chain_value
            else chain_label(0)
        )
        chain_msas[f"{base_name}{label}"] = chain_df

    return chain_msas


def build_multimer_csv(msa_data: dict, selected_msas: List[str]) -> pd.DataFrame:
    """Build a CSV-ready DataFrame from multiple stored MSAs with a chain column."""
    combined_dfs = []
    for idx, msa_name in enumerate(selected_msas):
        df = pd.DataFrame(msa_data[msa_name]).copy()
        df["chain"] = chain_label(idx)
        combined_dfs.append(df)

    if not combined_dfs:
        raise ValueError("No MSAs selected")

    return pd.concat(combined_dfs, ignore_index=True)


__all__ = [
    "read_a3m",
    "iter_a3m",
    "write_a3m",
    "encode_a3m",
    "decode_a3m",
    "read_fasta",
    "chain_label",
    "is_multimer_a3m_text",
    "parse_a3m",
    "combine_unpaired_a3m",
    "split_multimer_a3m_file",
    "read_a3m_with_chains",
    "split_dataframe_by_chain",
    "build_multimer_csv",
]
