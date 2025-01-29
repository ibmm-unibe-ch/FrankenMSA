"""
Main API functions
"""

from .msa import *
from pathlib import Path


def read_msa(file_path: str) -> "MSA":
    """
    Read an MSA from a file.

    Parameters
    ----------
    file_path : str
        Path to the MSA file. This can be any of:
        - a pickle file storing an MSA object
        - a FASTA or A3M or A2M file
        - a prefix for which `a3m`, `m8`, and `template` files exist.

    Returns
    -------
    MSA
        MSA object.
    """
    if file_path.endswith(".pkl"):
        return MSA.load(file_path)

    if (
        file_path.endswith(".a3m")
        or file_path.endswith(".a2m")
        or file_path.endswith(".fasta")
    ):
        msa = MSA()
        a3m = A3MAlignment.from_file(file_path)
        msa.alignment = a3m
        return msa

    if Path(file_path).suffix == "":
        msa = MSA.from_files(file_path)
        return msa
