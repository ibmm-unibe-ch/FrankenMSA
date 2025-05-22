"""
Cluster an MSA using KMeans
"""

from typing import List, Union
import pandas as pd
from sklearn.cluster import KMeans as SKLearnKMeans
from ..utils import seqtools
from .base import BaseClusterer, CLUSTER_ID_COL


def kmeans(
    sequences: Union[List[str], pd.DataFrame, pd.Series],
    n_clusters: int = 10,
    columns: List[str] = None,
    sequence_encoding: str = "onehot",
    *args,
    **kwargs,
) -> pd.DataFrame:
    """
    Cluster a list of sequences using KMeans.

    Parameters
    ----------
    sequences: List[str] or pd.DataFrame or pd.Series
        Sequences to cluster. If a DataFrame is provided, it must contain a column named "sequence".
        If a Series is provided, it should contain strings representing the sequences.
    n_clusters: int
        The number of clusters to form.
    columns: List[str], optional
        List of additional columns to consider when performing clustering. By default only the "sequence" column is used.
        These additional columns must be numerical!
    sequence_encoding: str, optional
        The encoding method to use for the sequences. By default, "onehot" encoding is used. Can be "onehot", or "numvector" (any method defined in by utils.seqtools.sequence_encodings).
    *args, kwargs
        Additional arguments to pass to the sklearn.cluster.KMeans constructor.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the clustered sequences. This will include a column named "cluster_id" indicating the cluster each sequence belongs to.
    """
    clusterer = KMeans()
    return clusterer.cluster(
        sequences, n_clusters, columns, sequence_encoding, *args, **kwargs
    )


class KMeans(BaseClusterer):
    """
    Cluster an MSA using KMeans
    """

    def cluster(
        self,
        sequences: Union[List[str], pd.DataFrame, pd.Series],
        n_clusters: int = 10,
        columns: List[str] = None,
        sequence_encoding: str = "onehot",
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Cluster a list of sequences using KMeans.

        Parameters
        ----------
        sequences: List[str] or pd.DataFrame or pd.Series
            Sequences to cluster. If a DataFrame is provided, it must contain a column named "sequence".
            If a Series is provided, it should contain strings representing the sequences.
        n_clusters: int
            The number of clusters to form.
        columns: List[str], optional
            List of additional columns to consider when performing clustering. By default only the "sequence" column is used.
            These additional columns must be numerical!
        sequence_encoding: str, optional
            The encoding method to use for the sequences. By default, "onehot" encoding is used. Can be "onehot", or "numvector" (any method defined in by utils.seqtools.sequence_encodings).
        *args, kwargs
            Additional arguments to pass to the sklearn.cluster.KMeans constructor.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the clustered sequences. This will include a column named "cluster_id" indicating the cluster each sequence belongs to.
        """
        # Precheck data
        msa = self._precheck_data(sequences)

        encoding_func = getattr(seqtools.sequence_encodings, sequence_encoding, None)
        if encoding_func is None:
            raise ValueError(f"Unknown sequence encoding method: {sequence_encoding}")

        encoded_sequences = encoding_func(msa["sequence"])
        if encoded_sequences.ndim > 2:
            encoded_sequences = encoded_sequences.reshape(
                encoded_sequences.shape[0], -1
            )
        if columns is not None:
            if not all(col in msa.columns for col in columns):
                raise ValueError(
                    f"Some columns specified in 'columns' are not present in the DataFrame: {columns}"
                )
            _clustering_data = pd.concat(
                [pd.DataFrame(encoded_sequences), msa[columns]], axis=1
            )
            _clustering_data = _clustering_data.to_numpy()

        else:
            _clustering_data = encoded_sequences

        if _clustering_data.ndim > 2:
            _clustering_data = _clustering_data.reshape(_clustering_data.shape[0], -1)

        kmeans = SKLearnKMeans(n_clusters=n_clusters, *args, **kwargs)
        msa[CLUSTER_ID_COL] = kmeans.fit_predict(_clustering_data)

        return msa.reset_index(drop=True)
