"""
Auxiliary functions for working with peptide sequences.
"""

import pandas as pd
from collections import Counter
from typing import List, Union, Iterable
import numpy as np

amino_acids_1letter = set("ACDEFGHIKLMNPQRSTVWY")
"""
Amino acids in one-letter code.
"""

missing_or_unknown = "X"
"""
Character to use for missing or unknown amino acids.
"""


def is_valid_peptide_sequence(seq: str) -> bool:
    """
    Check if a peptide sequence is valid

    Parameters
    ----------
    seq : str
        The peptide sequence to check

    Returns
    -------
    bool
        Whether the peptide sequence is valid
    """
    seq = seq.upper()
    return set(seq).issubset(amino_acids_1letter | set(missing_or_unknown))


def vet_sequence(seq: str) -> str:
    """
    Ensure a peptide sequence is standardized to uppercase and only valid characters

    Parameters
    ----------
    seq : str
        The peptide sequence to vet

    Returns
    -------
    str
        The vetted peptide sequence
    """
    seq = seq.upper()
    seq = "".join(aa if aa in amino_acids_1letter else missing_or_unknown for aa in seq)
    return seq


def consensus_sequence(seqs: pd.Series) -> str:
    """
    Compute the consensus sequence from a list of sequences.

    Parameters
    ----------
    seqs : pd.Series
        A pandas Series containing the sequences.

    Returns
    -------
    str
        The consensus sequence.
    """
    seqs = zip(*seqs)
    consensus = "".join(Counter(seq).most_common(1)[0][0] for seq in seqs)
    return consensus


amino_acid_alphabet = "ACDEFGHIKLMNPQRSTVWY-" + missing_or_unknown

amino_acid_mapping = {aa: i for i, aa in enumerate(amino_acid_alphabet)}


class sequence_encodings:

    @staticmethod
    def onehot(sequences: Iterable[str], max_length: int = None, squeeze: bool = False):
        """
        One-hot encode a list of sequences.

        Parameters
        ----------
        sequences : Iterable[str]
            A list of sequences to one-hot encode.
        max_length : int, optional
            The maximum length of the sequences. If None, the maximum length is determined from the input sequences.
        squeeze : bool, optional
            If False, the output will be a 3D array of shape (num_sequences, max_length, len(amino_acid_alphabet)).
            If True, the output will be a 2D array of shape (num_sequences, max_length * len(amino_acid_alphabet)).
            Default is False.


        Returns
        -------
        np.ndarray
            A numpy array containing the one-hot encoded sequences.

        """
        if max_length is None:
            max_length = max(len(seq) for seq in sequences)
        onehot = np.zeros(
            (len(sequences), max_length, len(amino_acid_alphabet)), dtype=np.float16
        )
        for i, seq in enumerate(sequences):
            for j, aa in enumerate(seq[:max_length]):
                if aa in amino_acid_mapping:
                    onehot[i, j, amino_acid_mapping[aa]] = 1.0
        if squeeze:
            onehot = onehot.reshape(len(sequences), -1)
        return onehot

    @staticmethod
    def numvector(sequences: Iterable[str], max_length: int = None):
        """
        Convert a list of sequences to a numerical representation. Each amino acid is represented by its index in the amino_acid_alphabet.
        The sequences are padded with -1.

        Parameters
        ----------
        sequences : Iterable[str]
            A list of sequences to convert.
        max_length : int, optional
            The maximum length of the sequences. If None, the maximum length is determined from the input sequences.

        Returns
        -------
        np.ndarray
            A numpy array containing the numerical representation of the sequences.
            The shape of the array is (num_sequences, max_length).
        """
        if max_length is None:
            max_length = max(len(seq) for seq in sequences)
        num_vector = np.full((len(sequences), max_length), -1, dtype=np.int8)
        for i, seq in enumerate(sequences):
            for j, aa in enumerate(seq[:max_length]):
                if aa in amino_acid_mapping:
                    num_vector[i, j] = amino_acid_mapping[aa]
        return num_vector
