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
    """Thin object wrapper around a pandas DataFrame-backed MSA.

    The class keeps the functional library modules as the implementation source
    of truth and mainly provides an object-oriented facade for working with an
    existing alignment.
    """

    def __init__(self, dataframe: pd.DataFrame):
        """Wrap an existing MSA DataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame representing the alignment. It is wrapped directly rather
            than copied.
        """
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("dataframe must be a pandas DataFrame")
        self._df = dataframe

    @classmethod
    def from_a3m(cls, path: str | Path) -> Self:
        """Create an MSA from an A3M file.

        See :func:`frankenmsa.utils.fileio.read_a3m`.
        """
        return cls(fileio.read_a3m(str(path)))

    @classmethod
    def from_csv(cls, path: str | Path, **kwargs) -> Self:
        """Create an MSA from a CSV file read with :func:`pandas.read_csv`."""
        return cls(pd.read_csv(path, **kwargs))

    @classmethod
    def from_a3m_string(cls, a3m_string: str) -> Self:
        """Create an MSA from in-memory A3M text.

        See :func:`frankenmsa.utils.fileio.decode_a3m`.
        """
        return cls(fileio.decode_a3m(a3m_string))

    @classmethod
    def combine(
        cls,
        msas: Iterable[MSA | pd.DataFrame],
        directions: list[str],
        horizontal_ranges: Optional[list[tuple[int, int]]] = None,
        vertical_ranges: Optional[list[tuple[int, int]]] = None,
    ) -> Self:
        """Combine multiple MSAs into a new wrapper instance.

        See :func:`frankenmsa.utils.msatools.combine_msa_operations`.
        """
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
        """Merge per-chain MSAs into a multimeric alignment.

        See :func:`frankenmsa.utils.msatools.merge_chains`.
        """
        frames = [
            msa.to_dataframe(copy=False) if isinstance(msa, MSA) else msa
            for msa in msas
        ]
        return cls(msatools.merge_chains(frames))

    def __len__(self) -> int:
        return len(self._df)

    def __add__(self, other) -> Self:
        """Return ``self.concat_horizontal(other)``."""
        return self.concat_horizontal(other)

    def __truediv__(self, other) -> Self:
        """Return ``self.concat_vertical(other)``."""
        return self.concat_vertical(other)

    def __getitem__(self, key) -> Self:
        """Return a sliced MSA using column-first indexing.

        Examples
        --------
        `msa[5:10]` slices sequence columns across all rows.
        `msa[5:10, 2:20]` slices sequence columns first and then rows.
        """
        column_selector = key
        row_selector = slice(None)

        if isinstance(key, tuple):
            if len(key) != 2:
                raise IndexError(
                    "MSA slicing supports at most two selectors: columns, rows"
                )
            column_selector, row_selector = key

        sliced_df = self._slice_rows(row_selector)
        sliced_df = self._slice_columns(sliced_df, column_selector)
        return MSA(sliced_df)

    def __repr__(self) -> str:
        return f"MSA(depth={self.depth}, columns={list(self._df.columns)!r})"

    @property
    def df(self) -> pd.DataFrame:
        """Return the wrapped DataFrame by reference."""
        return self._df

    @property
    def depth(self) -> int:
        """Return the number of rows in the alignment."""
        return len(self._df)

    @property
    def columns(self) -> list[str]:
        """Return the DataFrame column names."""
        return self._df.columns.tolist()

    @property
    def is_multimer(self) -> bool:
        """Return whether the wrapped MSA carries multimer metadata."""
        return "chain" in self._df.columns or "_multimer_header" in self._df.columns

    @property
    def query(self) -> Self:
        """Return the first row as a one-sequence MSA."""
        if self._df.empty:
            return MSA(self._df.iloc[0:0].reset_index(drop=True))
        return MSA(self._df.iloc[[0]].reset_index(drop=True))

    def copy(self) -> Self:
        """Return a deep-copied MSA wrapper."""
        return MSA(self._df.copy(deep=True))

    def to_dataframe(self, copy: bool = False) -> pd.DataFrame:
        """Expose the wrapped DataFrame.

        Parameters
        ----------
        copy : bool, default False
            If True, return a deep copy. Otherwise return the wrapped object.
        """
        return self._df.copy(deep=True) if copy else self._df

    def write_a3m(self, path: str | Path) -> Self:
        """Write the current MSA to an A3M file and return ``self``.

        See :func:`frankenmsa.utils.fileio.write_a3m`.
        """
        fileio.write_a3m(self._df, str(path))
        return self

    def to_a3m_string(self) -> str:
        """Encode the current MSA as A3M text.

        See :func:`frankenmsa.utils.fileio.encode_a3m`.
        """
        return fileio.encode_a3m(self._df)

    def to_csv(self, path: str | Path, **kwargs) -> Self:
        """Write the current MSA to CSV and return `self`."""
        self._df.to_csv(path, index=False, **kwargs)
        return self

    def concat_horizontal(self, other: MSA | pd.DataFrame) -> Self:
        """Return a new MSA by concatenating another alignment by columns.

        See :func:`frankenmsa.utils.msatools.combine_msa_operations` with
        ``direction="horizontal"``.
        """
        return self._concat_with(other, direction="horizontal")

    def concat_vertical(self, other: MSA | pd.DataFrame) -> Self:
        """Return a new MSA by stacking another alignment by rows.

        See :func:`frankenmsa.utils.msatools.combine_msa_operations` with
        ``direction="vertical"``.
        """
        return self._concat_with(other, direction="vertical")

    def _coerce_msa_input(self, other: MSA | pd.DataFrame) -> pd.DataFrame:
        """Normalize concat inputs to a DataFrame reference."""
        if isinstance(other, MSA):
            return other.df
        if isinstance(other, pd.DataFrame):
            return other
        raise TypeError("MSA concatenation requires another MSA or pandas DataFrame")

    def _concat_with(self, other: MSA | pd.DataFrame, direction: str) -> Self:
        """Return a new MSA by combining `self` with another alignment."""
        other_df = self._coerce_msa_input(other)
        combined = msatools.combine_msa_operations(
            [self._df, other_df],
            [direction, direction],
        )
        return MSA(combined)

    def _slice_rows(self, selector) -> pd.DataFrame:
        """Slice alignment rows with integer or slice semantics."""
        if isinstance(selector, slice):
            return self._df.iloc[selector].reset_index(drop=True)
        if isinstance(selector, int):
            return self._df.iloc[[selector]].reset_index(drop=True)
        raise TypeError("MSA row selection must use an int or slice")

    def _slice_columns(self, dataframe: pd.DataFrame, selector) -> pd.DataFrame:
        """Slice sequence characters while preserving the remaining columns."""
        if not isinstance(selector, (slice, int)):
            raise TypeError("MSA column selection must use an int or slice")

        result = dataframe.copy()
        if isinstance(selector, int):
            result["sequence"] = result["sequence"].str.get(selector).fillna("")
            return result

        result["sequence"] = result["sequence"].str.slice(
            selector.start, selector.stop, selector.step
        )
        return result

    def _apply_dataframe_method(self, func, *args, **kwargs) -> Self:
        """Apply an in-place style DataFrame transform and return `self`."""
        self._df = func(self._df, *args, **kwargs)
        return self

    def unify_length(self, sequence_length: int | str = "first") -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.unify_length`."""
        return self._apply_dataframe_method(msatools.unify_length, sequence_length)

    def slice_sequences(self, start: int, end: int) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.slice_sequences`."""
        return self._apply_dataframe_method(msatools.slice_sequences, start, end)

    def slice_rows(self, start: int = 0, end: Optional[int] = None) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.slice_rows`."""
        return self._apply_dataframe_method(msatools.slice_rows, start, end)

    def adjust_depth(self, depth: int) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.adjust_depth`."""
        return self._apply_dataframe_method(msatools.adjust_depth, depth)

    def crop_to_depth(self, depth: int) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.crop_to_depth`."""
        return self._apply_dataframe_method(msatools.crop_to_depth, depth)

    def extend_to_depth(self, depth: int) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.extend_to_depth`."""
        return self._apply_dataframe_method(msatools.extend_to_depth, depth)

    def drop_duplicates(self, keep_first: bool = True) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.drop_duplicates`."""
        return self._apply_dataframe_method(msatools.drop_duplicates, keep_first)

    def filter_gaps(self, allowed_gaps_fraction: float) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.filter_gaps`."""
        return self._apply_dataframe_method(msatools.filter_gaps, allowed_gaps_fraction)

    def filter_by_regex(
        self,
        pattern: str,
        method: str = "contains",
        inverse: bool = False,
    ) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.filter_by_regex`."""
        return self._apply_dataframe_method(
            msatools.filter_by_regex,
            pattern,
            method=method,
            inverse=inverse,
        )

    def filter_by_query(self, query_string: str) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.filter_by_query`."""
        return self._apply_dataframe_method(msatools.filter_by_query, query_string)

    def replace_characters(
        self,
        pattern: str,
        replacement: str,
        regex: bool = False,
    ) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.replace_characters`."""
        return self._apply_dataframe_method(
            msatools.replace_characters,
            pattern,
            replacement,
            regex=regex,
        )

    def replace_insertions_with_gaps(self) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.replace_insertions_with_gaps`."""
        return self._apply_dataframe_method(msatools.replace_insertions_with_gaps)

    def replace_unknown_with_gaps(self) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.replace_unknown_with_gaps`."""
        return self._apply_dataframe_method(msatools.replace_unknown_with_gaps)

    def uppercase_sequences(self) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.uppercase_sequences`."""
        return self._apply_dataframe_method(msatools.uppercase_sequences)

    def lowercase_sequences(self) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.lowercase_sequences`."""
        return self._apply_dataframe_method(msatools.lowercase_sequences)

    def sort_gaps(self, ascending: bool = True) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.sort_gaps`."""
        return self._apply_dataframe_method(msatools.sort_gaps, ascending=ascending)

    def sort_identity(self, ascending: bool = True) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.sort_identity`."""
        return self._apply_dataframe_method(msatools.sort_identity, ascending=ascending)

    def sort_by_column(
        self,
        column: str,
        ascending: bool = True,
        preserve_query: bool = True,
    ) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.sort_by_column`."""
        return self._apply_dataframe_method(
            msatools.sort_by_column,
            column,
            ascending=ascending,
            preserve_query=preserve_query,
        )

    def filter_identity(self, identity_threshold: float, method: str = "keep") -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.filter_identity`."""
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
        """Update ``self`` via :func:`frankenmsa.utils.msatools.shuffle_rows`."""
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
        """Update ``self`` via :func:`frankenmsa.utils.msatools.shuffle_msa`."""
        return self._apply_dataframe_method(
            msatools.shuffle_msa,
            start=start,
            end=end,
            preserve_gaps=preserve_gaps,
            random_state=random_state,
            inplace=False,
        )

    def insert_at(self, sequence: str, index: int, include_query: bool = True) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.insert_at`."""
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
        """Update ``self`` via :func:`frankenmsa.utils.msatools.remove_at`."""
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
        """Update ``self`` via :func:`frankenmsa.utils.msatools.replace_at`."""
        return self._apply_dataframe_method(
            msatools.replace_at,
            replacement,
            index,
            include_query=include_query,
        )

    def fix_at(self, indices: list[int]) -> Self:
        """Update ``self`` via :func:`frankenmsa.utils.msatools.fix_at`."""
        return self._apply_dataframe_method(msatools.fix_at, indices)

    def split_chains(self) -> list[Self]:
        """Split the wrapped multimer into one :class:`MSA` per chain.

        See :func:`frankenmsa.utils.msatools.split_chains`.
        """
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
        """Update ``self`` via :func:`frankenmsa.filter.hhsuite.hhfilter`."""
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
        """Update ``self`` via :meth:`frankenmsa.cluster.af_cluster.AFCluster.cluster`."""
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
        """Update ``self`` via :meth:`frankenmsa.cluster.kmeans.KMeans.cluster`."""
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
        """Update ``self`` via :func:`frankenmsa.cluster.ward.ward_merge_cluster_centroids`."""
        result = ward_module.ward_merge_cluster_centroids(
            self._df,
            n_clusters=n_clusters,
            encoding=encoding,
        )
        if result is None:
            raise ValueError(
                "Ward centroid merge requires an existing 'cluster_id' column."
            )
        self._df = result
        return self

    def gap_counts(self, normalize_length: str = "max") -> pd.Series:
        """Return :func:`frankenmsa.visual.summaries.gap_counts` for ``self``."""
        return summaries.gap_counts(self._df, normalize_length=normalize_length)

    def conservation_scores(self, normalize_length: str = "max") -> pd.Series:
        """Return :func:`frankenmsa.visual.summaries.conservation_scores` for ``self``."""
        return summaries.conservation_scores(
            self._df, normalize_length=normalize_length
        )

    def query_identity_scores(self, normalize_length: str = "max") -> pd.Series:
        """Return :func:`frankenmsa.visual.summaries.query_identity_scores` for ``self``."""
        return summaries.query_identity_scores(
            self._df, normalize_length=normalize_length
        )

    def compute_pca(self, encoding=None):
        """Return :func:`frankenmsa.visual.dimension_reduction.compute_PCA` for ``self``."""
        return dimension_reduction.compute_PCA(self._df, encoding=encoding)

    def visualise(self, backend: str = "matplotlib"):
        """Return :func:`frankenmsa.visual.alignment_chart.visualise_msa` for ``self``."""
        return alignment_chart.visualise_msa(self._df, backend=backend)

    def visualize(self, backend: str = "matplotlib"):
        """Return :func:`frankenmsa.visual.alignment_chart.visualize_msa` for ``self``."""
        return alignment_chart.visualize_msa(self._df, backend=backend)


__all__ = ["MSA"]
