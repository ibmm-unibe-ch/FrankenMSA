from __future__ import annotations

import numpy as np
import pandas as pd

from ..utils.msatools import unify_length


def gap_counts(msa: pd.DataFrame, normalize_length: str = "max") -> pd.Series:
    """Return the per-position gap counts for an MSA."""
    df = unify_length(msa.copy(), normalize_length)
    sequence_length = len(df["sequence"].iloc[0])
    counts = np.zeros(sequence_length)

    for sequence in df["sequence"]:
        counts += np.fromiter((1 if aa == "-" else 0 for aa in sequence), dtype=int)

    return pd.Series(counts, name="gap_count")


def conservation_scores(msa: pd.DataFrame, normalize_length: str = "max") -> pd.Series:
    """Return the per-position conservation fraction for an MSA."""
    df = unify_length(msa.copy(), normalize_length)
    sequence_length = len(df["sequence"].iloc[0])
    scores = np.zeros(sequence_length)

    for index in range(sequence_length):
        residues = df["sequence"].str.get(index)
        residue_counts = residues.value_counts()
        scores[index] = residue_counts.iloc[0] / len(residues)

    return pd.Series(scores, name="conservation")


def query_identity_scores(
    msa: pd.DataFrame,
    normalize_length: str = "max",
) -> pd.Series:
    """Return the per-position identity to the query row for an MSA."""
    df = unify_length(msa.copy(), normalize_length)
    sequence_length = len(df["sequence"].iloc[0])

    if len(df) <= 1:
        return pd.Series(np.ones(sequence_length), name="identity")

    query = df.iloc[0]["sequence"]
    rest = df.iloc[1:]
    scores = np.zeros(sequence_length)

    for index in range(sequence_length):
        residues = rest["sequence"].str.get(index)
        residue_counts = residues.value_counts()
        query_residue = query[index]
        if query_residue in residue_counts:
            scores[index] = residue_counts[query_residue] / len(residues)

    return pd.Series(scores, name="identity")


__all__ = [
    "gap_counts",
    "conservation_scores",
    "query_identity_scores",
]
