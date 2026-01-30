"""
Functions to read and write files.
"""

import pandas as pd
from typing import Tuple


def read_a3m(filename: str) -> pd.DataFrame:
    """
    Read an A3M file and return a DataFrame with the sequences and their headers.

    Parameters
    ----------
    filename : str
        The path to the A3M file.

    Returns
    -------
    pd.DataFrame
        A DataFrame with the sequences and their headers.
    """

    # Initialize lists to store headers and sequences
    headers = []
    sequences = []

    # Open the A3M file and read it line by line
    with open(filename, "r") as f:
        for line in f:
            # Strip whitespace from the line
            line = line.strip()
            if not line:
                continue

            # If the line starts with '>', it's a header
            if line.startswith(">"):
                headers.append(line[1:])
            # If it starts with '#', it's a comment/multimer header, skip for dataframe
            elif line.startswith("#"):
                continue
            else:
                sequences.append(line)
    out = pd.DataFrame({"header": headers, "sequence": sequences})
    return out


def iter_a3m(filename: str) -> Tuple[str]:
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
            # Strip whitespace from the line
            line = line.strip()
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

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue  # Skip multimer header in dataframe body

        if line.startswith(">"):
            headers.append(line[1:])
        else:
            sequences.append(line)

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
        line = line.strip()
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

__all__ = [
    "read_a3m",
    "iter_a3m",
    "write_a3m",
    "encode_a3m",
    "decode_a3m",
    "read_fasta",
]
