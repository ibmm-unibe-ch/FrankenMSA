"""
Basic classes for alignment algorithms.
"""

from typing import Iterable, Union
import pandas as pd


class MSAFactory:
    """
    Base class for MSA generators.
    """
    def __init__(self):
        self.msa = None

    def align(self, sequences: Union[pd.DataFrame, Iterable[str]], *args, **kwargs) -> pd.Series:
        """
        Align a list of sequences.

        Parameters
        ----------
        sequences: pd.DataFrame or Iterable or str
            Sequences to align. If a DataFrame is provided, it must contain a column named "sequence".
            If an iterable is provided, it should contain strings representing the sequences.
        *args, **kwargs
            Additional arguments to pass to the alignment algorithm.
            
        Returns
        -------
        pd.Series
            Series containing the aligned sequences.
        """
        raise NotImplementedError()

    def __call__(self, *args, **kwds):
        return self.align(*args, **kwds)
    
    def __repr__(self):
        return f"{self.__class__.__name__}()"   