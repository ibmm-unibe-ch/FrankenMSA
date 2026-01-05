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
    "shuffle_msa",
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


def shuffle_msa(
    df: pd.DataFrame,
    start: Optional[int] = None,
    end: Optional[int] = None,
    preserve_gaps: bool = True,
    random_state: Optional[int] = None,
    inplace: bool = False,
) -> pd.DataFrame:
    """
    Column-wise shuffling for an MSA DataFrame while keeping the first sequence (query) fixed.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
        All sequences must have the same length.
    start : int, optional
        Start position (0-based, inclusive) of the region to shuffle. Defaults to 0.
    end : int, optional
        End position (0-based, exclusive) of the region to shuffle. Defaults to sequence length.
    preserve_gaps : bool, default True
        If True, gaps ('-') keep their original row positions in each column and only
        non-gap residues among non-query rows are shuffled. If False, gaps participate
        in the shuffling (still excluding the query row).
    random_state : int, optional
        Seed for reproducibility.
    inplace : bool, default False
        If True, modify the input DataFrame in place and return it. Otherwise, return a copy.

    Returns
    -------
    pd.DataFrame
        DataFrame with column-shuffled non-query sequences in the selected range.

    Notes
    -----
    - The first row is treated as the query sequence and is not modified.
    - This function does NOT pad or crop sequences. If lengths differ, a ValueError is raised.
      You may call `unify_length` beforehand if needed.
    """
    if "sequence" not in df.columns:
        raise ValueError("DataFrame must contain a 'sequence' column.")

    # Ensure all sequences have the same length
    lengths = df["sequence"].str.len().unique()
    if len(lengths) != 1:
        raise ValueError(
            "All sequences must have the same length. Consider calling `unify_length` first."
        )
    L = int(lengths[0])

    # Resolve slice bounds
    s = 0 if start is None else int(start)
    e = L if end is None else int(end)
    if not (0 <= s <= e <= L):
        raise ValueError(f"Invalid range: start={s}, end={e}, sequence_length={L}")

    # Prepare RNG
    import random

    rng = random.Random(random_state)

    # Work on a copy unless inplace
    out = df if inplace else df.copy()

    # Fast path: nothing to do if depth < 2 or zero-length slice
    if len(out) <= 1 or s == e:
        return out.reset_index(drop=True)

    # Convert sequences to list-of-chars for in-place edits
    seq_lists = out["sequence"].tolist()
    seq_lists = [list(seq) for seq in seq_lists]  # depth x L

    # Shuffle per column in [s, e)
    # Row 0 is query and remains unchanged
    depth = len(seq_lists)
    for col in range(s, e):
        # Collect indices of rows eligible for shuffling (exclude query row 0)
        non_query_rows = list(range(1, depth))

        if preserve_gaps:
            # Only shuffle among non-gap residues; keep gaps at their rows
            nongap_rows = [r for r in non_query_rows if seq_lists[r][col] != "-"]
            if len(nongap_rows) > 1:
                residues = [seq_lists[r][col] for r in nongap_rows]
                rng.shuffle(residues)
                for r, aa in zip(nongap_rows, residues):
                    seq_lists[r][col] = aa
            # else: 0 or 1 residue -> nothing to permute
        else:
            # Shuffle everything (including '-') among non-query rows
            if len(non_query_rows) > 1:
                residues = [seq_lists[r][col] for r in non_query_rows]
                rng.shuffle(residues)
                for r, aa in zip(non_query_rows, residues):
                    seq_lists[r][col] = aa

    # Stitch back to strings
    out["sequence"] = ["".join(chars) for chars in seq_lists]
    return out.reset_index(drop=True)


def insert_at(
    df: pd.DataFrame, sequence: str, index: int, include_query: bool = True
) -> pd.DataFrame:
    """
    Insert a sequence at a given position shifting existing residues down.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    sequence: str
        The sequence to insert.
    index: int
        The index at which to insert the sequence.
    include_query: bool, optional
        If True, the index includes the query sequence (first row). If False, the index excludes the query sequence. If False this likely leads to misalignments!

    Returns
    -------
    pd.DataFrame
        DataFrame with the specified sequence inserted at the given position.
    """
    sequence_col = "sequence"
    if sequence_col not in df.columns:
        raise ValueError(f"DataFrame must contain a '{sequence_col}' column.")

    length = len(sequence)
    if not include_query:
        query_row = df.iloc[[0]]
        df = df.iloc[1:].reset_index(drop=True)
        df = insert_at(df, sequence, index, include_query=True)
        df = pd.concat([query_row, df], ignore_index=True)
        return df.reset_index(drop=True)

    df[sequence_col] = (
        df[sequence_col].str.slice(0, index)
        + sequence
        + df[sequence_col].str.slice(index)
    )
    return df


def remove_at(
    df: pd.DataFrame,
    start: int,
    end: int = None,
    include_query: bool = True,
) -> pd.DataFrame:
    """
    Remove a slice from sequences in a DataFrame.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    start: int
        The starting index for the slice to remove.
    end: int
        The ending index for the slice to remove. If None, only the position at 'start' is removed.
    include_query: bool, optional
        If True, also remove the slice from the query sequence (first row). If False, the query sequence remains unchanged.
        If the query remains unchanged the resulting MSA may be misaligned!

    Returns
    -------
    pd.DataFrame
        DataFrame with the specified slice removed from sequences.
    """
    if "sequence" not in df.columns:
        raise ValueError("DataFrame must contain a 'sequence' column.")

    if end is None:
        end = start + 1

    if not include_query:
        query_row = df.iloc[[0]]
        df = df.iloc[1:].reset_index(drop=True)
        df = remove_at(df, start, end, include_query=True)
        df = pd.concat([query_row, df], ignore_index=True)
        return df.reset_index(drop=True)

    df["sequence"] = df["sequence"].str.slice(0, start) + df["sequence"].str.slice(end)
    return df


def replace_at(
    df: pd.DataFrame,
    replacement: str,
    index: int,
    include_query: bool = False,
) -> pd.DataFrame:
    """
    Replace a slice in sequences in a DataFrame with a given replacement string.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    replacement: str
        The replacement string.
    index: int
        The index at which to replace the slice (0-based, start of the slice).
    include_query: bool, optional
        If True, also replace the slice in the query sequence (first row). If False, the query sequence remains unchanged.

    Returns
    -------
    pd.DataFrame
        DataFrame with the specified slice replaced in sequences.
    """
    if "sequence" not in df.columns:
        raise ValueError("DataFrame must contain a 'sequence' column.")
    length = len(replacement)
    if not include_query:
        query_row = df.iloc[[0]]
        df = df.iloc[1:].reset_index(drop=True)
        df = replace_at(df, replacement, index, include_query=True)
        df = pd.concat([query_row, df], ignore_index=True)
        return df.reset_index(drop=True)

    df["sequence"] = (
        df["sequence"].str.slice(0, index)
        + replacement
        + df["sequence"].str.slice(index + length)
    )
    return df


def fix_at(df: pd.DataFrame, indices: list[int]):
    """
    Propagate the residues in the query sequence (first row) to all other sequences at the specified indices.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing sequences. Must contain a column named "sequence".
    indices: list[int]
        List of indices (0-based) at which to fix the residues.

    Returns
    -------
    pd.DataFrame
        DataFrame with residues fixed at the specified indices.
    """
    if "sequence" not in df.columns:
        raise ValueError("DataFrame must contain a 'sequence' column.")

    query_sequence = df["sequence"].iloc[0]
    seq_lists = df["sequence"].tolist()
    seq_lists = [list(seq) for seq in seq_lists]  # depth x L

    for index in indices:
        residue = query_sequence[index]
        for r in range(1, len(seq_lists)):
            seq_lists[r][index] = residue

    df["sequence"] = ["".join(chars) for chars in seq_lists]
    return df.reset_index(drop=True)
