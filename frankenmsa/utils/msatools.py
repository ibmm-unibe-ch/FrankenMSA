"""
General funcionality for MSA manipulation.
"""

import pandas as pd
from typing import Optional, Union

__all__ = [
    "unify_length",
    "crop_to_depth",
    "drop_duplicates",
]


def unify_length(df: pd.DataFrame, sequence_length: int = None):
    """
    Unify the length of sequences in a DataFrame by cropping or padding with gaps.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    sequence_length: int, optional
        The length to which all sequences should be unified.
        If None, the length of the first sequence in the DataFrame is used.

    Returns
    -------
    pd.DataFrame
        DataFrame with unified sequence lengths.
    """
    if "sequence" not in df.columns:
        raise ValueError("DataFrame must contain a 'sequence' column.")

    if sequence_length is None:
        sequence_length = len(df["sequence"].iloc[0])

    df["sequence"] = df["sequence"].str.ljust(sequence_length, "-")
    df["sequence"] = df["sequence"].str.slice(0, sequence_length)
    return df


def crop_to_depth(
    df: pd.DataFrame,
    depth: int,
) -> pd.DataFrame:
    """
    Crop sequences in a DataFrame to a specified depth.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    depth: int
        The depth to which all sequences should be cropped.

    Returns
    -------
    pd.DataFrame
        DataFrame with cropped sequences.
    """
    if "sequence" not in df.columns:
        raise ValueError("DataFrame must contain a 'sequence' column.")

    return df.iloc[:depth].reset_index(drop=True)


def drop_duplicates(
    df: pd.DataFrame,
    keep_first: bool = True,
) -> pd.DataFrame:
    """
    Drop duplicate sequences from a DataFrame.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    keep_first: bool, optional
        If True, keep the first occurrence of each duplicate. If False, keep the last occurrence.

    Returns
    -------
    pd.DataFrame
        DataFrame with duplicates removed.
    """
    sequence_col = "sequence"
    if sequence_col not in df.columns:
        raise ValueError(f"DataFrame must contain a '{sequence_col}' column.")

    return df.drop_duplicates(
        subset=sequence_col, keep="first" if keep_first else "last"
    ).reset_index(drop=True)


def filter_gaps(df: pd.DataFrame, allowed_gaps_faction: float) -> pd.DataFrame:
    """
    Filter out sequences that contain gaps.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    allowed_gaps_faction: float
        The maximum fraction of gaps allowed in a sequence. Sequences with a higher fraction of gaps will be removed.

    Returns
    -------
    pd.DataFrame
        DataFrame with sequences containing gaps removed.
    """
    sequence_col = "sequence"
    if sequence_col not in df.columns:
        raise ValueError(f"DataFrame must contain a '{sequence_col}' column.")

    if not (0 <= allowed_gaps_faction <= 1):
        raise ValueError("allowed_gaps_faction must be between 0 and 1.")

    gap_count = df[sequence_col].str.count("-")
    sequence_length = df[sequence_col].str.len()
    gap_fraction = gap_count / sequence_length
    filtered_df = df[gap_fraction <= allowed_gaps_faction].reset_index(drop=True)
    return filtered_df
