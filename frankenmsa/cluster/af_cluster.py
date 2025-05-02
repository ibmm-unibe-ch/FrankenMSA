"""
Cluster an MSA using DBSCAN as described by


[Wayment-Steele, H. K. et al. Predicting multiple conformations via sequence clustering and AlphaFold2. Nature 625, 832–839 (2024)](https://www.nature.com/articles/s41586-023-06832-9)

"""

from afcluster import AFCluster as _AFCluster
from afcluster import afcluster as _afcluster

from typing import List, Union
import pandas as pd


class AFCluster(_AFCluster):

    def cluster(
        self,
        sequences: Union[List[str], pd.DataFrame, pd.Series],
        eps: float = None,
        min_samples: int = 3,
        columns: List[str] = None,
        consensus_sequence: bool = True,
        levenshtein: bool = True,
        verbose: bool = False,
    ) -> pd.DataFrame:
        """
        Cluster an MSA using DBSCAN

        Parameters
        ----------
        sequences : List or DataFrame or Series
            The MSA to cluster. This can be a list of (aligned) sequences, a pandas DataFrame with a "sequence" column, or a pandas Series containing sequences.
            In any case, the first sequence is interpreted as the query sequence.
        eps : float
            Epsilon value for DBSCAN clustering. If a search was done beforehand, the best value is remembered by the class.
        min_samples : int
            The minimum number of sequences in a cluster for the clsuter to be accepted.
        columns : List[str]
            If a dataframe is passed, additional columns can also be included in the clustering.
            In these cases the columns must be numeric!
        consensus_sequence : bool
            If True, compute the consensus sequence for each cluster and add it to the output daraframe as column "consensus_sequence".
        levenshtein : bool
            If True, compute the levenshtein distance to the query sequence and the consensus sequence for each cluster and add it to the output dataframe as columns "levenshtein_query" and "levenshtein_consensus".

        Returns
        -------
        pd.DataFrame
            The clustered MSA as a pandas DataFrame. This will include a "sequence" and "cluster_id" column.s
        """
        return super().cluster(
            msa=sequences,
            eps=eps,
            min_samples=min_samples,
            columns=columns,
            max_gap_frac=1,
            resample=False,
            resample_frac=None,
            consensus_sequence=consensus_sequence,
            levenshtein=levenshtein,
            verbose=verbose,
        )


def afcluster(
    sequences: Union[List[str], pd.DataFrame, pd.Series],
    eps: float = None,
    min_samples: int = 3,
    columns: list = None,
    consensus_sequence: bool = True,
    levenshtein: bool = True,
    gridsrearch_eps_range=(3, 20),
    gridsrearch_eps_step=0.5,
    gridsearch_eps_mode: str = "fast",
    gridsearch_eps_data_frac: float = 0.55,
    gridsearch_eps_desired_clusters: int = "max",
    n_processes: int = 1,
    verbose: bool = False,
) -> Union[pd.DataFrame, List[pd.DataFrame]]:
    """
    Cluster an MSA using DBSCAN

    Parameters
    ----------
    sequences : List or DataFrame or Series
        The MSA to cluster. This can be a list of (aligned) sequences, a pandas DataFrame with a "sequence" column, or a pandas Series containing sequences.
        In any case, the first sequence is interpreted as the query sequence.
    eps : float
        Epsilon value to use for DBSCAN.
        If none is provided, a gridsearch is performed to find the best value.
        For this, the eps_range and eps_step parameters are used.
    min_samples : int
        The minimum number of sequences in a cluster for the cluster to be accepted.
    columns : List[str]
        If a dataframe is passed, additional columns can also be included in the clustering.
        In these cases the columns must be numeric! By default, only the "sequence" column is used, any columns that are provided here are added to the clustering data.
    consensus_sequence : bool
        If True, compute the consensus sequence for each cluster and add it to the output dataframe as column "consensus_sequence".
    levenshtein : bool
        If True, compute the levenshtein distance to the query sequence and the consensus sequence for each cluster and add it to the output dataframe as columns "levenshtein_query" and "levenshtein_consensus".
    gridsearch_eps_range : tuple
        The range of epsilon values to use for the gridsearch.
        Only used if eps is None.
    gridsearch_eps_step : float
        The step size for the gridsearch.
        Only used if eps is None.
    gridsearch_eps_mode : str
        The implementation of the gridsearch to find an epsilon value.
        This can be "fast" (uses a very small fraction of data and repeated sampling) or "exhaustive" (uses a larger fraction of data and no repeated sampling).
    gridsearch_eps_data_frac : float
        The fraction of data to use for the gridsearch.
        Only used if gridsearch_eps_mode is "exhaustive". If you are trying to aim for a specific number of desired clusters values over 0.5 are recommended for better results.
        If gridsearch_eps_mode is "fast" this is flatly set to 0.05.
    gridsearch_eps_desired_clusters : int
        By default epsilon gridsearch tries to maximize the number of clusters.
        If you want to limit the number of clusters you can add a specific number here. In this case the search will return the epsilon value
        that achieves the number of clusters closest to the desired number. Note that this works best with exhaustive search and a high data fraction.
    n_processes : int
        The number of processes to use for the gridsearch.
        Only used if eps is None.
    verbose : bool
        If True, print progress messages.
        If False, no messages are printed.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the clustered sequences. This will include a "sequence" and "cluster_id" column.
    """
    clusterer = AFCluster()
    df = clusterer._precheck_data(sequences)
    if eps is None:
        if gridsearch_eps_mode == "fast":
            # the use of 0.05 comes from the default settings
            # in afcluster.search_eps.gridsearch_fast
            # to avoid double-reduction we need to maintain all the data at first
            gridsearch_eps_data_frac = 1.0

        eps = clusterer.gridsearch_eps(
            msa=df,
            desired_clusters=gridsearch_eps_desired_clusters,
            min_eps=gridsrearch_eps_range[0],
            max_eps=gridsrearch_eps_range[1],
            step=gridsrearch_eps_step,
            data_frac=gridsearch_eps_data_frac,
            max_gap_frac=1,
            min_samples=min_samples,
            n_processes=n_processes,
            mode=gridsearch_eps_mode,
        )

    out = clusterer.cluster(
        sequences=df,
        eps=eps,
        min_samples=min_samples,
        columns=columns,
        consensus_sequence=consensus_sequence,
        levenshtein=levenshtein,
        verbose=verbose,
    )
    return out


# aliases

dbscan = afcluster

DBScan = AFCluster
