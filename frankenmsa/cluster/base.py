from typing import List, Union
import pandas as pd


CLUSTER_ID_COL = "cluster_id"
"""
The name of the column in the DataFrame that will contain the cluster IDs.
"""


class BaseClusterer:
    """
    Base class for clustering algorithms.
    """

    def cluster(
        self, sequences: Union[List[str], pd.DataFrame, pd.Series], *args, **kwargs
    ) -> pd.DataFrame:
        """
        Cluster a list of sequences.

        Parameters
        ----------
        sequences: List[str] or pd.DataFrame or pd.Series
            Sequences to cluster. If a DataFrame is provided, it must contain a column named "sequence".
            If a Series is provided, it should contain strings representing the sequences.
        *args, **kwargs
            Additional arguments to pass to the clustering algorithm.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the clustered sequences. This will include a column named "cluster_id" indicating the cluster each sequence belongs to.
        """
        raise NotImplementedError()

    __call__ = cluster

    @staticmethod
    def _precheck_data(msa):
        if len(msa) < 2:
            raise ValueError(
                "The MSA must contain at least 2 sequences to perform clustering."
            )
        if not isinstance(msa, (list, tuple, set, pd.DataFrame, pd.Series)):
            raise TypeError(
                f"msa must be of type list, DataFrame or Series, got ({type(msa)})"
            )
        if isinstance(msa, (list, tuple, set, pd.Series)):
            if not all(isinstance(seq, str) for seq in msa):
                raise TypeError(
                    "If msa is a list, tuple, or Series, it must contain only strings (sequences)."
                )
            df = pd.DataFrame({"sequence": msa})

        elif isinstance(msa, pd.DataFrame):
            if "sequence" not in msa.columns:
                raise ValueError(
                    "If msa is a DataFrame, it must contain a 'sequence' column."
                )
            df = msa
        return df

    def __repr__(self):
        return f"{self.__class__.__name__}()"
