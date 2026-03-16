"""
Basic classes for augmentation algorithms.
"""

from typing import Iterable, Union
import pandas as pd


class AugmentationFactory:
    """
    Base class for MSA augmentation methods.
    """
    def __init__(self):
        self.msa = None

    def augment(self, sequence:str, *args, **kwargs) -> pd.Series:
        """Augmentation of sequences
        
        Parameters
        ----------
            sequence (str): input sequence to augment.
            *args, **kwargs: Additional arguments to pass to the augmentation algorithm.

        Raises:
            NotImplementedError: 

        Returns
        -------
        pd.DataFrame
            DataFrame containing the augmented sequences.
        """
        raise NotImplementedError()

    def __call__(self, *args, **kwds):
        return self.augment(*args, **kwds)
    
    def __repr__(self):
        return f"{self.__class__.__name__}()"   