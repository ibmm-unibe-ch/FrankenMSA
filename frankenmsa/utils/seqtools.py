"""
Auxiliary functions for working with peptide sequences.
"""

import pandas as pd
from collections import Counter
from typing import List, Union, Iterable
import numpy as np
import string


__all__ = [
    "is_valid_peptide_sequence",
    "vet_sequence",
    "consensus_sequence",
]

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

def get_encoding_func(encoding_name):
    if encoding_name is None:
        encoding_name = "onehot"
    encoding_func = getattr(sequence_encodings, encoding_name, None)
    if encoding_func is None:
            raise ValueError(f"Unknown sequence encoding method: {encoding_name}")
    return encoding_func


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
    
    @staticmethod
    def esm(sequences: Iterable[str], max_length:int =None):
        """
        Generate ESM3 embeddings for a list of protein sequences.
        
        Args:
            sequences: List of protein sequence strings to embed
                        
        Returns:
            List of embedding tensors for each input sequence
            
        Raises:
            RuntimeError: If CUDA is requested but not available
            ValueError: If sequences are invalid or empty
        """
        import torch
        from esm.models.esmc import ESMC
        from esm.sdk.api import ESMProtein, LogitsConfig
        if not sequences:
            raise ValueError("No sequences provided for embedding")
        
        # Initialize ESM3 model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        client = ESMC.from_pretrained("esmc_300m").to(device)
        embeddings = []
        if max_length is None:
            max_length = max(len(seq) for seq in sequences)
        for sequence in sequences:
            if not sequence or not isinstance(sequence, str):
                raise ValueError(f"Invalid sequence: {sequence}")
                
            protein = ESMProtein(sequence=sequence[:max_length])
            protein_tensor = client.encode(protein)
            
            # Get logits and embeddings
            logits_output = client.logits(
                protein_tensor, 
                LogitsConfig(sequence=True, return_embeddings=True)
            )
            
            # logits_output.embeddings shape: [1, length+2, 960]
            # (batch=1, seq_length=sequence_length+beginining+cls token, embedding_dim=960)

            # Use mean pooling as recommended by ESM authors
            # See: https://github.com/evolutionaryscale/esm/issues/116
            #      https://github.com/evolutionaryscale/esm/issues/162
            embeddings.append(torch.mean(logits_output.embeddings[0], dim=0))
        
        return embeddings.squeeze().numpy()

def multimer_chain_splitting(msa_df, chain_lengths, new_main_key, msa_data):    
    start = 0
    split_keys = []
    alphabet = string.ascii_uppercase
    
    for i, length in enumerate(chain_lengths):
        end = start + length
        chain_seqs = [s[start:end] for s in msa_df["sequence"]]
        
        # Update header for split file: first header becomes chain index
        new_headers = list(msa_df["header"])
        if len(new_headers) > 0:
            new_headers[0] = str(101 + i)
        
        chain_df = pd.DataFrame({
            "header": new_headers, 
            "sequence": chain_seqs
        })
        
        chain_suffix = alphabet[i] if i < 26 else str(i+1)
        split_key = f"{new_main_key}_chain{chain_suffix}"
        
        msa_data[split_key] = chain_df.to_dict("list")
        split_keys.append(split_key)
        start = end
    
    split_msg = f" Also generated split files: {', '.join(split_keys)}."
    return split_msg, msa_data