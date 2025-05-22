"""
General funcionality for MSA manipulation.
"""

import pandas as pd
from typing import Optional, Union

__all__ = [
    "unify_length",
    "crop_to_depth",
    "drop_duplicates",
    "filter_gaps",
    "sort_gaps",
    "sort_identity",
    "filter_identity",
    "slice_sequences",
    "adjust_depth",
    "extend_to_depth",
    "crop_to_depth",
]


def unify_length(df: pd.DataFrame, sequence_length: int = "first"):
    """
    Unify the length of sequences in a DataFrame by cropping or padding with gaps.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    sequence_length: int, optional
        The length to which all sequences should be unified.
        If "first", the length of the first sequence in the DataFrame is used.
        If "max", the length of the longest sequence in the DataFrame is used.
        If "min", the length of the shortest sequence in the DataFrame is used.

    Returns
    -------
    pd.DataFrame
        DataFrame with unified sequence lengths.
    """
    if "sequence" not in df.columns:
        raise ValueError("DataFrame must contain a 'sequence' column.")

    if sequence_length == "first":
        sequence_length = len(df["sequence"].iloc[0])
    elif sequence_length == "max":
        sequence_length = df["sequence"].str.len().max()
    elif sequence_length == "min":
        sequence_length = df["sequence"].str.len().min()
    elif not isinstance(sequence_length, int):
        raise ValueError("sequence_length must be 'first', 'max', 'min' or an integer.")

    df["sequence"] = df["sequence"].str.ljust(sequence_length, "-")
    df["sequence"] = df["sequence"].str.slice(0, sequence_length)
    return df


def slice_sequences(
    df: pd.DataFrame,
    start: int,
    end: int,
) -> pd.DataFrame:
    """
    Slice sequences in a DataFrame to a specified range.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    start: int
        The starting index for slicing.
    end: int
        The ending index for slicing.

    Returns
    -------
    pd.DataFrame
        DataFrame with sliced sequences.
    """
    if "sequence" not in df.columns:
        raise ValueError("DataFrame must contain a 'sequence' column.")

    df["sequence"] = df["sequence"].str.slice(start, end)
    return df


def adjust_depth(
    df: pd.DataFrame,
    depth: int,
) -> pd.DataFrame:
    """
    Adjust the depth of sequences in a DataFrame to a specified depth. This will either
    drop sequences if the DataFrame is too long or extend it by repeating entries if it's too short.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    depth: int
        The depth to which all sequences should be adjusted.

    Returns
    -------
    pd.DataFrame
        DataFrame with adjusted sequences.
    """
    if "sequence" not in df.columns:
        raise ValueError("DataFrame must contain a 'sequence' column.")

    if len(df) < depth:
        return extend_to_depth(df, depth)
    else:
        return crop_to_depth(df, depth)


def crop_to_depth(
    df: pd.DataFrame,
    depth: int,
) -> pd.DataFrame:
    """
    Drop sequences in a DataFrame to reach a specified depth.
    If the DataFrame is already shorter than the specified depth, it will be returned unchanged.

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
    if depth < 0:
        return df
    return df.iloc[:depth].reset_index(drop=True)


def extend_to_depth(
    df: pd.DataFrame,
    depth: int,
) -> pd.DataFrame:
    """
    Extend sequences in a DataFrame to a specified depth by repeating entries.
    If the DataFrame is already longer than the specified depth, it will be returned unchanged.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    depth: int
        The depth to which all to extend.

    Returns
    -------
    pd.DataFrame
        DataFrame with extended sequences.
    """
    if "sequence" not in df.columns:
        raise ValueError("DataFrame must contain a 'sequence' column.")

    if depth < len(df):
        return df

    # Calculate the number of times to repeat each sequence
    repeat_count = (depth + len(df) - 1) // len(df)

    # Repeat the DataFrame and reset the index
    extended_df = pd.concat([df] * repeat_count, ignore_index=True).iloc[:depth]
    return extended_df.reset_index(drop=True)


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


def sort_gaps(
    df: pd.DataFrame,
    ascending: bool = True,
) -> pd.DataFrame:
    """
    Sort sequences in a DataFrame by the number of gaps.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    ascending: bool, optional
        If True, sort in ascending order. If False, sort in descending order.

    Returns
    -------
    pd.DataFrame
        DataFrame sorted by the number of gaps.
    """
    sequence_col = "sequence"
    if sequence_col not in df.columns:
        raise ValueError(f"DataFrame must contain a '{sequence_col}' column.")

    query = df.iloc[[0]]
    _df = df.iloc[1:]
    gap_count = _df[sequence_col].str.count("-")
    sorted_df = (
        _df.assign(gap_count=gap_count)
        .sort_values(by="gap_count", ascending=ascending)
        .drop(columns=["gap_count"])
    )
    sorted_df = pd.concat([query, sorted_df], ignore_index=True)
    return sorted_df.reset_index(drop=True)


def sort_identity(
    df: pd.DataFrame,
    ascending: bool = True,
) -> pd.DataFrame:
    """
    Sort sequences in a DataFrame by sequence identity to the query sequence (first sequence).

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    ascending: bool, optional
        If True, sort in ascending order. If False, sort in descending order.

    Returns
    -------
    pd.DataFrame
        DataFrame sorted by the number of identical residues.
    """
    sequence_col = "sequence"
    if sequence_col not in df.columns:
        raise ValueError(f"DataFrame must contain a '{sequence_col}' column.")

    query_sequence = df.iloc[[0]]
    _df = df.iloc[1:]
    q = query_sequence[sequence_col]
    identity_count = _df[sequence_col].apply(
        lambda x: sum(a == b for a, b in zip(q, x))
    )
    sorted_df = (
        _df.assign(identity_count=identity_count)
        .sort_values(by="identity_count", ascending=ascending)
        .drop(columns=["identity_count"])
    )
    sorted_df = pd.concat([query_sequence, sorted_df], ignore_index=True)
    return sorted_df.reset_index(drop=True)


def filter_identity(
    df: pd.DataFrame,
    identity_threshold: float,
    method: str = "keep",
) -> pd.DataFrame:
    """
    Filter sequences in a DataFrame by sequence identity to the query sequence (first sequence).

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    identity_threshold: float
        The minimum fraction of identical residues required for a sequence to be considered.
    method: str, optional
        The method to use for filtering. If "keep", sequences with identity above the threshold are kept.
        If "remove", sequences with identity below the threshold are removed.

    Returns
    -------
    pd.DataFrame
        DataFrame with sequences filtered by identity.
    """
    sequence_col = "sequence"
    if sequence_col not in df.columns:
        raise ValueError(f"DataFrame must contain a '{sequence_col}' column.")

    if not (0 <= identity_threshold <= 1):
        raise ValueError("identity_threshold must be between 0 and 1.")

    query_sequence = df.iloc[[0]]
    q = query_sequence[sequence_col]
    _df = df.iloc[1:]
    identity_count = _df[sequence_col].apply(
        lambda x: sum(a == b for a, b in zip(q, x))
    )
    sequence_length = _df[sequence_col].str.len()
    identity_fraction = identity_count / sequence_length
    if method == "keep":
        filtered_df = _df[identity_fraction >= identity_threshold].reset_index(
            drop=True
        )
    elif method == "remove":
        filtered_df = _df[identity_fraction < identity_threshold].reset_index(drop=True)
    else:
        raise ValueError("method must be 'keep' or 'remove'.")
    filtered_df = pd.concat([query_sequence, filtered_df], ignore_index=True)
    filtered_df = filtered_df.reset_index(drop=True)
    return filtered_df
