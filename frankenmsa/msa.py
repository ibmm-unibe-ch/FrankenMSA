from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Self

import pandas as pd

from .cluster import af_cluster
from .cluster import kmeans as kmeans_module
from .cluster import ward as ward_module
from .filter import hhsuite as hhsuite_module
from .utils import fileio
from .utils import msatools
from .visual import alignment_chart
from .visual import dimension_reduction
from .visual import summaries


class MSA:
    """Thin object wrapper around a pandas DataFrame-backed MSA."""

    def __init__(self, dataframe: pd.DataFrame):
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("dataframe must be a pandas DataFrame")
        self._df = dataframe

    @classmethod
    def from_a3m(cls, path: str | Path) -> Self:
        return cls(fileio.read_a3m(str(path)))

    @classmethod
    def from_csv(cls, path: str | Path, **kwargs) -> Self:
        return cls(pd.read_csv(path, **kwargs))

    @classmethod
    def from_a3m_string(cls, a3m_string: str) -> Self:
        return cls(fileio.decode_a3m(a3m_string))

    @classmethod
    def combine(
        cls,
        msas: Iterable[MSA | pd.DataFrame],
        directions: list[str],
        horizontal_ranges: Optional[list[tuple[int, int]]] = None,
        vertical_ranges: Optional[list[tuple[int, int]]] = None,
    ) -> Self:
        frames = [
            msa.to_dataframe(copy=False) if isinstance(msa, MSA) else msa
            for msa in msas
        ]
        combined = msatools.combine_msa_operations(
            frames,
            directions,
            horizontal_ranges=horizontal_ranges,
            vertical_ranges=vertical_ranges,
        )
        return cls(combined)

    @classmethod
    def merge_chains(cls, msas: Iterable[MSA | pd.DataFrame]) -> Self:
        frames = [
            msa.to_dataframe(copy=False) if isinstance(msa, MSA) else msa
            for msa in msas
        ]
        return cls(msatools.merge_chains(frames))

    def __len__(self) -> int:
        return len(self._df)

    def __add__(self, other) -> Self:
        return self.concat_horizontal(other)

    def __truediv__(self, other) -> Self:
        return self.concat_vertical(other)

    def __getitem__(self, key) -> Self:
        column_selector = key
        row_selector = slice(None)

        if isinstance(key, tuple):
            if len(key) != 2:
                raise IndexError("MSA slicing supports at most two selectors: columns, rows")
            column_selector, row_selector = key

        sliced_df = self._slice_rows(row_selector)
        sliced_df = self._slice_columns(sliced_df, column_selector)
        return MSA(sliced_df)

    def __repr__(self) -> str:
        return f"MSA(depth={self.depth}, columns={list(self._df.columns)!r})"

    @property
    def df(self) -> pd.DataFrame:
        return self._df

    @property
    def depth(self) -> int:
        return len(self._df)

    @property
    def columns(self) -> list[str]:
        return self._df.columns.tolist()

    @property
    def is_multimer(self) -> bool:
        return "chain" in self._df.columns or "_multimer_header" in self._df.columns

    @property
    def query(self) -> Self:
        if self._df.empty:
            return MSA(self._df.iloc[0:0].reset_index(drop=True))
        return MSA(self._df.iloc[[0]].reset_index(drop=True))

    def copy(self) -> Self:
        return MSA(self._df.copy(deep=True))

    def to_dataframe(self, copy: bool = False) -> pd.DataFrame:
        return self._df.copy(deep=True) if copy else self._df

    def write_a3m(self, path: str | Path) -> Self:
        fileio.write_a3m(self._df, str(path))
        return self

    def to_a3m_string(self) -> str:
        return fileio.encode_a3m(self._df)

    def to_csv(self, path: str | Path, **kwargs) -> Self:
        self._df.to_csv(path, index=False, **kwargs)
        return self

    def concat_horizontal(self, other: MSA | pd.DataFrame) -> Self:
        return self._concat_with(other, direction="horizontal")

    def concat_vertical(self, other: MSA | pd.DataFrame) -> Self:
        return self._concat_with(other, direction="vertical")

    def _coerce_msa_input(self, other: MSA | pd.DataFrame) -> pd.DataFrame:
        if isinstance(other, MSA):
            return other.df
        if isinstance(other, pd.DataFrame):
            return other
        raise TypeError("MSA concatenation requires another MSA or pandas DataFrame")

    def _concat_with(self, other: MSA | pd.DataFrame, direction: str) -> Self:
        other_df = self._coerce_msa_input(other)
        combined = msatools.combine_msa_operations(
            [self._df, other_df],
            [direction, direction],
        )
        return MSA(combined)

    def _slice_rows(self, selector) -> pd.DataFrame:
        if isinstance(selector, slice):
            return self._df.iloc[selector].reset_index(drop=True)
        if isinstance(selector, int):
            return self._df.iloc[[selector]].reset_index(drop=True)
        raise TypeError("MSA row selection must use an int or slice")

    def _slice_columns(self, dataframe: pd.DataFrame, selector) -> pd.DataFrame:
        if not isinstance(selector, (slice, int)):
            raise TypeError("MSA column selection must use an int or slice")

        result = dataframe.copy()
        if isinstance(selector, int):
            result["sequence"] = result["sequence"].str.get(selector).fillna("")
            return result

        result["sequence"] = result["sequence"].str.slice(selector.start, selector.stop, selector.step)
        return result

    def _apply_dataframe_method(self, func, *args, **kwargs) -> Self:
        self._df = func(self._df, *args, **kwargs)
        return self

    def unify_length(self, sequence_length: int | str = "first") -> Self:
        return self._apply_dataframe_method(msatools.unify_length, sequence_length)

    def slice_sequences(self, start: int, end: int) -> Self:
        return self._apply_dataframe_method(msatools.slice_sequences, start, end)

    def slice_rows(self, start: int = 0, end: Optional[int] = None) -> Self:
        return self._apply_dataframe_method(msatools.slice_rows, start, end)

    def adjust_depth(self, depth: int) -> Self:
        return self._apply_dataframe_method(msatools.adjust_depth, depth)

    def crop_to_depth(self, depth: int) -> Self:
        return self._apply_dataframe_method(msatools.crop_to_depth, depth)

    def extend_to_depth(self, depth: int) -> Self:
        return self._apply_dataframe_method(msatools.extend_to_depth, depth)

    def drop_duplicates(self, keep_first: bool = True) -> Self:
        return self._apply_dataframe_method(msatools.drop_duplicates, keep_first)

    def filter_gaps(self, allowed_gaps_fraction: float) -> Self:
        return self._apply_dataframe_method(msatools.filter_gaps, allowed_gaps_fraction)

    def filter_by_regex(
        self,
        pattern: str,
        method: str = "contains",
        inverse: bool = False,
    ) -> Self:
        return self._apply_dataframe_method(
            msatools.filter_by_regex,
            pattern,
            method=method,
            inverse=inverse,
        )

    def filter_by_query(self, query_string: str) -> Self:
        return self._apply_dataframe_method(msatools.filter_by_query, query_string)

    def replace_characters(
        self,
        pattern: str,
        replacement: str,
        regex: bool = False,
    ) -> Self:
        return self._apply_dataframe_method(
            msatools.replace_characters,
            pattern,
            replacement,
            regex=regex,
        )

    def replace_insertions_with_gaps(self) -> Self:
        return self._apply_dataframe_method(msatools.replace_insertions_with_gaps)

    def replace_unknown_with_gaps(self) -> Self:
        return self._apply_dataframe_method(msatools.replace_unknown_with_gaps)

    def uppercase_sequences(self) -> Self:
        return self._apply_dataframe_method(msatools.uppercase_sequences)

    def lowercase_sequences(self) -> Self:
        return self._apply_dataframe_method(msatools.lowercase_sequences)

    def sort_gaps(self, ascending: bool = True) -> Self:
        return self._apply_dataframe_method(msatools.sort_gaps, ascending=ascending)

    def sort_identity(self, ascending: bool = True) -> Self:
        return self._apply_dataframe_method(msatools.sort_identity, ascending=ascending)

    def sort_by_column(
        self,
        column: str,
        ascending: bool = True,
        preserve_query: bool = True,
    ) -> Self:
        return self._apply_dataframe_method(
            msatools.sort_by_column,
            column,
            ascending=ascending,
            preserve_query=preserve_query,
        )

    def filter_identity(self, identity_threshold: float, method: str = "keep") -> Self:
        return self._apply_dataframe_method(
            msatools.filter_identity,
            identity_threshold,
            method=method,
        )

    def shuffle_rows(
        self,
        random_state: Optional[int] = None,
        preserve_query: bool = True,
    ) -> Self:
        return self._apply_dataframe_method(
            msatools.shuffle_rows,
            random_state=random_state,
            preserve_query=preserve_query,
        )

    def shuffle_msa(
        self,
        start: Optional[int] = None,
        end: Optional[int] = None,
        preserve_gaps: bool = True,
        random_state: Optional[int] = None,
    ) -> Self:
        return self._apply_dataframe_method(
            msatools.shuffle_msa,
            start=start,
            end=end,
            preserve_gaps=preserve_gaps,
            random_state=random_state,
            inplace=False,
        )

    def insert_at(self, sequence: str, index: int, include_query: bool = True) -> Self:
        return self._apply_dataframe_method(
            msatools.insert_at,
            sequence,
            index,
            include_query=include_query,
        )

    def remove_at(
        self,
        start: int,
        end: Optional[int] = None,
        include_query: bool = True,
    ) -> Self:
        return self._apply_dataframe_method(
            msatools.remove_at,
            start,
            end,
            include_query=include_query,
        )

    def replace_at(
        self,
        replacement: str,
        index: int,
        include_query: bool = False,
    ) -> Self:
        return self._apply_dataframe_method(
            msatools.replace_at,
            replacement,
            index,
            include_query=include_query,
        )

    def fix_at(self, indices: list[int]) -> Self:
        return self._apply_dataframe_method(msatools.fix_at, indices)

    def split_chains(self) -> list[Self]:
        return [MSA(frame) for frame in msatools.split_chains(self._df)]

    def hhfilter(
        self,
        diff: int,
        max_pairwise_identity: int = 100,
        min_query_coverage: int = 50,
        min_query_identity: int = 0,
        min_query_score: float = -20,
        target_diversity: int = 0,
        *args,
        **kwargs,
    ) -> Self:
        self._df = hhsuite_module.hhfilter(
            self._df,
            diff,
            max_pairwise_identity=max_pairwise_identity,
            min_query_coverage=min_query_coverage,
            min_query_identity=min_query_identity,
            min_query_score=min_query_score,
            target_diversity=target_diversity,
            *args,
            **kwargs,
        )
        return self

    def cluster_afcluster(
        self,
        eps: float | None = None,
        min_samples: int = 3,
        columns: Optional[list[str]] = None,
        consensus_sequence: bool = True,
        levenshtein: bool = True,
        verbose: bool = False,
    ) -> Self:
        clusterer = af_cluster.AFCluster()
        self._df = clusterer.cluster(
            self._df,
            eps=eps,
            min_samples=min_samples,
            columns=columns,
            consensus_sequence=consensus_sequence,
            levenshtein=levenshtein,
            verbose=verbose,
        )
        return self

    def cluster_kmeans(
        self,
        n_clusters: int = 10,
        columns: Optional[list[str]] = None,
        encoding: str = "onehot",
        *args,
        **kwargs,
    ) -> Self:
        clusterer = kmeans_module.KMeans()
        self._df = clusterer.cluster(
            self._df,
            n_clusters=n_clusters,
            columns=columns,
            encoding=encoding,
            *args,
            **kwargs,
        )
        return self

    def cluster_ward_merge(self, n_clusters: int, encoding: str | None = None) -> Self:
        result = ward_module.ward_merge_cluster_centroids(
            self._df,
            n_clusters=n_clusters,
            encoding=encoding,
        )
        if result is None:
            raise ValueError("Ward centroid merge requires an existing 'cluster_id' column.")
        self._df = result
        return self

    def gap_counts(self, normalize_length: str = "max") -> pd.Series:
        return summaries.gap_counts(self._df, normalize_length=normalize_length)

    def conservation_scores(self, normalize_length: str = "max") -> pd.Series:
        return summaries.conservation_scores(self._df, normalize_length=normalize_length)

    def query_identity_scores(self, normalize_length: str = "max") -> pd.Series:
        return summaries.query_identity_scores(self._df, normalize_length=normalize_length)

    def compute_pca(self, encoding=None):
        return dimension_reduction.compute_PCA(self._df, encoding=encoding)

    def visualise(self, backend: str = "matplotlib"):
        return alignment_chart.visualise_msa(self._df, backend=backend)

    def visualize(self, backend: str = "matplotlib"):
        return alignment_chart.visualize_msa(self._df, backend=backend)


__all__ = ["MSA"]