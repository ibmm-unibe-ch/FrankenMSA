"""
Auxiliary functions for working with peptide sequences.
"""

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