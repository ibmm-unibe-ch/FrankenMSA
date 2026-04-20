from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd

from .base import CLUSTER_ID_COL
from .ward import ward_merge_cluster_centroids
from ..visual.dimension_reduction import compute_PCA


def numeric_column_options(df: pd.DataFrame) -> list[dict]:
    columns = df.select_dtypes(include=["number"]).columns.tolist()
    return [{"label": col, "value": col} for col in columns]


def cluster_dropdown_options(
    df: pd.DataFrame,
    cluster_column: str = CLUSTER_ID_COL,
    label_prefix: str = "Cluster",
    include_all: bool = True,
) -> list[dict]:
    if cluster_column not in df.columns:
        return []

    clusters = df[cluster_column].dropna().unique().tolist()
    options = [
        {"label": f"{label_prefix} {cluster}", "value": cluster} for cluster in clusters
    ]
    if include_all:
        options.insert(0, {"label": "All", "value": "all"})
    return options


def selected_cluster_ids(
    df: pd.DataFrame,
    selected: Optional[Iterable],
    cluster_column: str = CLUSTER_ID_COL,
) -> list:
    if cluster_column not in df.columns or not selected:
        return []

    selected = list(selected)
    if "all" in selected:
        return df[cluster_column].dropna().unique().tolist()
    return selected


def save_cluster_subsets(
    msa_data: dict,
    main_msa: str,
    cluster_column: str = CLUSTER_ID_COL,
    selected: Optional[Iterable] = None,
    name_template: str = "{main}_cluster_{cluster}",
) -> dict:
    if not msa_data or not main_msa:
        return msa_data

    df = pd.DataFrame.from_dict(msa_data[main_msa])
    cluster_ids = selected_cluster_ids(df, selected, cluster_column=cluster_column)
    if not cluster_ids:
        return msa_data

    updated = dict(msa_data)
    for cluster_id in cluster_ids:
        subset = df[df[cluster_column] == cluster_id]
        name = name_template.format(main=main_msa, cluster=cluster_id)
        updated[name] = subset.to_dict("list")
    return updated


def run_ward_centroid_merge(
    df: pd.DataFrame,
    n_clusters: int,
    encoding: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    return ward_merge_cluster_centroids(df, n_clusters=n_clusters, encoding=encoding)


def run_ward_clustering(
    df: pd.DataFrame,
    n_clusters: int,
    encoding: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    return run_ward_centroid_merge(df, n_clusters=n_clusters, encoding=encoding)


def cluster_pca_projection(
    df: pd.DataFrame,
    encoding: Optional[str] = None,
) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    return compute_PCA(df, encoding)
