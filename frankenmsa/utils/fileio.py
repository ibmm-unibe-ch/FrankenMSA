"""
Functions to read and write files.
"""

import pandas as pd
import numpy as np
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
            # If the line starts with '>', it's a header
            if line.startswith(">"):
                headers.append(line[1:])
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

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to write to the A3M file.
    filename : str
        The path to the A3M file.
    """

    if "header" in df.columns:
        format_entry = lambda index, row: f">{row['header']}\n{row['sequence']}\n"
    else:
        format_entry = lambda index, row: f">seq{index}\n{row['sequence']}\n"

    # Open the A3M file for writing
    with open(filename, "w") as f:

        # Iterate over the rows of the DataFrame
        for index, row in df.iterrows():
            # Write the formatted entry to the file
            f.write(format_entry(index, row))


__all__ = [
    "read_a3m",
    "iter_a3m",
    "write_a3m",
]
